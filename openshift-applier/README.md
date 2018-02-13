# OpenShift Applier for JupyterHub

Uses the [openshift-applier](https://github.com/redhat-cop/casl-ansible/tree/master/roles/openshift-applier) model for Infrastructure-as-Code (IaC) to fully automate the instructions in [the main README](../README.md).

## Usage

1. `[openshift-applier]$ ansible-galaxy install -r requirements.yml --roles-path=roles`
2. `[openshift-applier]$ ansible-playbook roles/casl-ansible/playbooks/openshift-cluster-seed.yml -i inventory/`

## Running a Subset of the Inventory 

Pass in the `-e filter_tags=tag1,tag2` flag to the `ansible-playbook` command.