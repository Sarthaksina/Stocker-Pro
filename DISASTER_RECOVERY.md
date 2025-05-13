# STOCKER Pro Disaster Recovery Plan

This document outlines the disaster recovery procedures for the STOCKER Pro API infrastructure. It provides guidelines for responding to various disaster scenarios, ensuring minimal downtime and data loss.

## Table of Contents

- [Recovery Objectives](#recovery-objectives)
- [Backup Strategies](#backup-strategies)
- [Disaster Scenarios](#disaster-scenarios)
- [Recovery Procedures](#recovery-procedures)
- [Testing and Validation](#testing-and-validation)
- [Roles and Responsibilities](#roles-and-responsibilities)

## Recovery Objectives

### Recovery Time Objective (RTO)

- **Production Environment**: 1 hour
- **Staging Environment**: 4 hours

### Recovery Point Objective (RPO)

- **Production Environment**: 15 minutes
- **Staging Environment**: 1 hour

## Backup Strategies

### Database Backups

#### Automated Backups

The PostgreSQL database is backed up using the following mechanisms:

1. **Daily Full Backups**: Automated through the Kubernetes CronJob (`backup-cronjob.yaml`)
   - Schedule: Daily at 2:00 AM
   - Retention: 7 days
   - Storage: Persistent volume with cloud provider snapshots

2. **Point-in-Time Recovery (PITR)**:
   - WAL archiving enabled
   - Continuous archiving to cloud storage
   - Allows recovery to any point within the retention period

3. **Cloud Provider Snapshots**:
   - RDS automated backups (if using RDS)
   - Retention: 30 days for production, 7 days for staging

### Infrastructure Backups

1. **Kubernetes State**:
   - `etcd` backups: Daily
   - Kubernetes resource definitions: Stored in Git repository
   - Helm release history: Stored in Git repository

2. **Configuration Backups**:
   - All configuration stored in Git repository
   - Infrastructure as Code (Terraform) in version control
   - Secrets managed through secure vault (AWS Secrets Manager or HashiCorp Vault)

3. **Application Code**:
   - Stored in Git repository
   - Docker images in container registry with versioning

## Disaster Scenarios

### Scenario 1: Database Corruption or Data Loss

**Impact**: Loss of data integrity or complete data loss

**Recovery Strategy**:
1. Identify the extent of corruption/loss
2. Stop all write operations to the database
3. Restore from the most recent backup
4. Apply WAL logs for point-in-time recovery
5. Validate data integrity
6. Resume normal operations

### Scenario 2: Kubernetes Cluster Failure

**Impact**: Application downtime, potential service disruption

**Recovery Strategy**:
1. Determine the cause of failure
2. If node-level issue: Allow Kubernetes to reschedule pods
3. If cluster-level issue: Restore cluster from Terraform
4. Apply Kubernetes manifests from Git repository
5. Verify application health and functionality

### Scenario 3: Cloud Provider Region Outage

**Impact**: Complete service outage in the affected region

**Recovery Strategy**:
1. Activate multi-region failover (if configured)
2. Deploy infrastructure in secondary region using Terraform
3. Restore database from latest backup to secondary region
4. Update DNS to point to secondary region
5. Verify application health and functionality

### Scenario 4: Accidental Deletion or Misconfiguration

**Impact**: Service disruption or partial functionality loss

**Recovery Strategy**:
1. Identify the affected resources
2. Restore configuration from Git repository
3. Apply correct configuration using Terraform and Kubernetes manifests
4. Verify application health and functionality

## Recovery Procedures

### Database Recovery

#### Restoring from Daily Backup

```bash
# List available backups
kubectl exec -n stocker-production $(kubectl get pod -n stocker-production -l app=stocker-db -o jsonpath='{.items[0].metadata.name}') -- ls -la /backups

# Restore from a specific backup
kubectl exec -n stocker-production $(kubectl get pod -n stocker-production -l app=stocker-db -o jsonpath='{.items[0].metadata.name}') -- bash -c "gunzip -c /backups/stocker-db-YYYYMMDD-HHMMSS.sql.gz | psql -U stocker stocker_db"
```

#### Point-in-Time Recovery

```bash
# For RDS
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier stocker-pro-production \
  --target-db-instance-identifier stocker-pro-production-recovery \
  --restore-time "YYYY-MM-DDThh:mm:ssZ"
```

### Kubernetes Cluster Recovery

#### Using Terraform to Recreate the Cluster

```bash
# Navigate to Terraform directory
cd terraform

# Initialize Terraform
terraform init \
  -backend-config="bucket=stocker-pro-terraform-state" \
  -backend-config="key=stocker-pro/production/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=stocker-pro-terraform-locks"

# Apply Terraform configuration
terraform apply -var-file=production.tfvars
```

#### Redeploying Applications

```bash
# Update kubeconfig
aws eks update-kubeconfig --name stocker-pro-production --region us-east-1

# Apply Kubernetes manifests
cd kubernetes/overlays/production
kubectl apply -k .
```

### Multi-Region Failover

#### Activating Secondary Region

```bash
# Deploy infrastructure in secondary region
cd terraform
terraform init \
  -backend-config="bucket=stocker-pro-terraform-state" \
  -backend-config="key=stocker-pro/production-dr/terraform.tfstate" \
  -backend-config="region=us-west-2" \
  -backend-config="dynamodb_table=stocker-pro-terraform-locks"

terraform apply -var-file=production-dr.tfvars

# Update DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id ZXXXXXXXXXXXXX \
  --change-batch file://dns-failover.json
```

## Testing and Validation

### Regular DR Testing Schedule

- **Database Restore Test**: Monthly
- **Cluster Recovery Test**: Quarterly
- **Multi-Region Failover Test**: Semi-annually

### Validation Procedures

1. **Database Validation**:
   - Verify data integrity
   - Run application-specific validation queries
   - Verify data consistency across services

2. **Application Validation**:
   - Run health check endpoints
   - Verify API functionality
   - Test critical business flows
   - Validate metrics and monitoring

3. **Performance Validation**:
   - Compare performance metrics with baseline
   - Verify response times are within acceptable thresholds

## Roles and Responsibilities

### Disaster Recovery Team

| Role | Responsibilities |
|------|------------------|
| DR Coordinator | Overall coordination of recovery efforts |
| Database Administrator | Database backup and recovery |
| DevOps Engineer | Infrastructure and Kubernetes recovery |
| Application Developer | Application validation and troubleshooting |
| QA Engineer | Testing and validation of recovered systems |

### Communication Plan

1. **Internal Communication**:
   - Use dedicated Slack channel (#disaster-recovery)
   - Regular status updates (every 30 minutes during active recovery)
   - Post-incident review meeting

2. **External Communication**:
   - Update status page
   - Notify customers through email/support channels
   - Provide estimated resolution time

## Appendix

### Recovery Checklist

- [ ] Assess the disaster impact and scope
- [ ] Declare disaster and activate DR plan
- [ ] Assemble DR team
- [ ] Execute appropriate recovery procedures
- [ ] Validate recovered systems
- [ ] Communicate status to stakeholders
- [ ] Return to normal operations
- [ ] Conduct post-incident review
- [ ] Update DR plan based on lessons learned

### Important Contacts

| Service | Contact Information |
|---------|----------------------|
| Cloud Provider Support | support@provider.com, 1-800-xxx-xxxx |
| Database Support | db-support@provider.com |
| Security Team | security@company.com |
| DR Coordinator | dr-coordinator@company.com |

### Reference Documentation

- [Kubernetes Backup and Restore Documentation](https://kubernetes.io/docs/tasks/administer-cluster/)
- [PostgreSQL Backup and Recovery](https://www.postgresql.org/docs/current/backup.html)
- [AWS Disaster Recovery](https://aws.amazon.com/disaster-recovery/)
- [Terraform Documentation](https://www.terraform.io/docs)
