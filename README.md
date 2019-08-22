# CPD Watson Machine Learning Quick Start

The CPD Watson Machine Learning Quick Start demonstrates use of PostgreSQL, Watson Machine Learning and MongoDB on Cloud Pak for Data. 
In this example we have one application producing events from reefer refrigeration containers capturing key data points such as temperature, humidity, cumulative_power_consumption the data is stores in a PostgreSQL database.
The second application reads the data from the PostgreSQL database and sends it to a Watson Machine Learning scoring model to determine whether the device requires maintenance, the results are stored in a MongoDB database.
                                                                                                                                                           
## Getting started

### Installing the Watson Assistant add-on on IBM Cloud Pak for Data 

Make your data ready for an AI and multicloud world. Cloud Pak for Data System is an all-in-one cloud-native Data and AI platform in a box, providing a pre-configured, governed, and secure environment to collect, organize and analyze data. [Learn more](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/overview/overview.html).

Installing Cloud Pak for Data on OpenShift- [Instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/install/ovu.html)

Installing the Watson Machine Learning add-on - [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/dsx/wmlservices.html)

Installing the PostgreSQL add-on [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/admin/create-db.html) see the PostgreSQL section.

Installing the MondoDB add-on - [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/admin/create-db.html) see the MongoDB section.


### Creating a project

After logging in with `oc login`, if you don't have an existing project, create a new project.

        $ oc new-project my-project --display-name="My Project"

Set your current project, for example:

        $ oc project my-project

### Creating the app from a template

Create the app from the [cpd-quick-start-watson-machine-learning.json](cpd-quick-start-watson-machine-learning.json) template by using the `-f` flag and pointing the tool at a path to the template file. Learn more about [OpenShift templates](https://docs.openshift.com/enterprise/3.0/dev_guide/templates.html#dev-guide-templates).

First, list the parameters that you can override:

        $ oc process --parameters -f https://raw.githubusercontent.com/estherhi/cpd-quick-start-watson-machine-learning/master/cpd-quick-start-watson-machine-learning.json

### required parameters

notice the `WORKSPACE_ID` optional parameter - you can start this app with an existing workspace, if left blank the first existing workspace will be used, or a new workspace will be created. [How to find existing workspace ID](#how-to-find-existing-workspace-id)

Create the app from the template:

        $ oc new-app -f \
        https://raw.githubusercontent.com/estherhi/cpd-quick-start-watson-machine-learning/master/cpd-quick-start-watson-machine-learning.json \
        -p POSTGRESQL_HOST=postgresql.project-from-office.svc \
        -p POSTGRESQL_USER=postgres \
        -p POSTGRESQL_PASSWORD=devx \
        -p POSTGRESQL_DATABASE=sampledb \
        -p MONGODB_HOST=mongodb.project-from-office.svc \
        -p MONGODB_USER=mongodb \
        -p MONGODB_PASSWORD=devx \
        -p MONGODB_DATABASE=sampledb \
        -p ICP4D_CLUSTER_HOST=icp4d-contest2-master-1.fyre.ibm.com \
        -p ICP4D_CLUSTER_USER=admin \
        -p ICP4D_CLUSTER_PASSWORD=password 

#### Build the app

`oc new-app` will kick off a build once all required dependencies are confirmed.

Check the status of your new nodejs app with the command:

        $ oc status
        
        
Which should return something like:

       In project project-from-office on server https://192.168.64.3:8443
     
       svc/watson-machine-learning-event-scorer - 172.30.223.123:8080 -> 3000
         dc/watson-machine-learning-event-scorer deploys istag/watson-machine-learning-event-scorer:latest <-
           bc/watson-machine-learning-event-scorer source builds https://github.com/estherhi/cpd-quick-start-watson-machine-learning on openshift/python:3.6 
             build #1 failed 40 seconds ago
           deployment #1 waiting on image or update      
        
        
If the build is not yet started (you can check by running `oc get builds`), start one and stream the logs with:

        $ oc start-build watson-machine-learning-event-scorer --follow
        
#### Deploy the app

Deployment happens automatically once the new application image is available.  To monitor its status either watch the web console or execute `oc get pods` to see when the pod is up.  Another helpful command is

        $ oc get svc
        
#### Routing


#### Success

You should now have two applications one producing data and storing it in the PostgreSQL database you had defined. The other application reading the PostgreSQL data, scoring it using Watson Machine Learning and storing hte resulsts in the MongoDB database you defined.

#### Pushing updates

Assuming you used the URL of your own forked repository, we can easily push changes and simply repeat the steps above which will trigger the newly built image to be deployed.
You can also define [Webhook Triggers](https://docs.openshift.com/container-platform/3.5/dev_guide/builds/triggering_builds.html#webhook-triggers) to trigger a new build when a repository is updated, using the `GITHUB_WEBHOOK_SECRET` or `GENERIC_WEBHOOK_SECRET` template parameters.

### Testing the app


### How to find existing workspace ID

1. Click on your Watson Assistance instance.

1. From the **Manage** page, click **Launch tool**.

1. Click the dots in the upper right hand corner for the workspace you want and click **View details**.

1. Copy the `Workspace ID` and paste this as a quickstart `WORKSPACE_ID` parameter value.


### Running locally


### Known issues


## License

 
