# Watson Machine Learning Quickstart

The Watson Machine Learning Quickstart demonstrates use of PostgreSQL, Watson Machine Learning, and MongoDB on Cloud Pak for Data to continuously enrich enterprise data with machine learning insights. 
This quickstart will get you up and running on any OpenShift cluster including a local [minishift](https://www.okd.io/minishift) running on your machine.

In this example, we have one microservice producing simulated refrigeration container (reefer) telemetry events that include temperature, humidity, cumulative power consumption, etc. The events are persisted in a PostgreSQL database.
A second microservice polls the telemetry data, applies a machine learning model to determine whether or not a given refrigeration unit requires maintenance, and stores the results in a MongoDB collection.
The most recent results are displayed in a simple web application. 

![Diagram](readme_images/arch_diagram.jpg)
                     
## Getting started

### Installing the Watson Assistant add-on on IBM Cloud Pak for Data 

Make your data ready for an AI and multicloud world. Cloud Pak for Data System is an all-in-one cloud-native Data and AI platform in a box, providing a pre-configured, governed, and secure environment to collect, organize and analyze data. [Learn more](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/overview/overview.html).

Installing Cloud Pak for Data on OpenShift- [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/install/ovu.html)

Installing the Watson Machine Learning add-on - [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/dsx/wmlservices.html)

Installing the PostgreSQL add-on [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/admin/create-db.html) see the PostgreSQL section.

Installing the MongoDB add-on [instructions](https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/zen/admin/create-db.html) see the MongoDB section.

### Create your own copy of this repo
Fork a copy of this repo

### Creating a project

After logging in with `oc login`, ensure that you have a project set up. If not, create one as follows:

        $ oc new-project watson-machine-learning-project --display-name="Watson Machine Learning Project"

That's it, project has been created. Ensure that your current project is set:

        $ oc project watson-machine-learning-project
        
### Creating the app from a template

The template for this example is located at [cpd-quick-start-watson-machine-learning.json](cpd-quick-start-watson-machine-learning.json).

First, list the available parameters:

        $ oc process --parameters -f https://raw.githubusercontent.com/estherhi/cpd-quick-start-watson-machine-learning/master/openshift/templates/cpd-quick-start-watson-machine-learning.json
        
The following parameters are required:   
  1.  POSTGRESQL_HOST
  2.  POSTGRESQL_USER
  3.  POSTGRESQL_PASSWORD
  4.  POSTGRESQL_DATABASE_NAME
  5.  MONGODB_HOST
  6.  MONGODB_USER 
  7.  MONGODB_PASSWORD
  8.  MONGODB_DATABASE
  9.  ICP4D_CLUSTER_HOST
  10. ICP4D_CLUSTER_USER
  11. ICP4D_CLUSTER_PASSWORD
        
Create the app from the template and specify the source url to be your forked repo:

        $ oc new-app -f \
        https://raw.githubusercontent.com/estherhi/cpd-quick-start-watson-machine-learning/master/openshift/templates/cpd-quick-start-watson-machine-learning.json \
        -p POSTGRESQL_HOST=<POSTGRESQL_HOST> \
        -p POSTGRESQL_USER=<POSTGRESQL_USER> \
        -p POSTGRESQL_PASSWORD=<POSTGRESQL_PASSWORD> \
        -p POSTGRESQL_DATABASE=<POSTGRESQL_DATABASE_NAME>\
        -p MONGODB_HOST=<MONGO_HOST> \
        -p MONGODB_USER=<MONGO_USER> \
        -p MONGODB_PASSWORD=<MONGO_PASSWORD> \
        -p MONGODB_DATABASE=<MONGO_DATABASE_NAME> \
        -p ICP4D_CLUSTER_HOST=<ICP4D_CLUSTER_HOST> \
        -p ICP4D_CLUSTER_USER=<ICP4D_CLUSTER_USER> \
        -p ICP4D_CLUSTER_PASSWORD=<ICP4D_CLUSTER_PASSWORD> 
        
`oc new-app` will kick off a build once all required dependencies are confirmed.        

#### Check the status


Check the status of your new nodejs app with the command:

        $ oc status
        
        
Which should return something like:

        In project Watson Machine Learning Project (watson-machine-learning-project) on server https://10.2.2.2:8443

         svc/watson-assistant-quickstart - 172.30.108.183:8080
          dc/watson-assistant-quickstart deploys istag/watson-assistant-quickstart:latest <-
            bc/watson-assistant-quickstart source builds https://github.ibm.com/icp4d-devex-prototype/cpd-quickstart-watson-assistant on openshift/nodejs:10
              build #1 running for 7 seconds
            deployment #1 waiting on image or update        
        

        
Which should return something like:

       In project e2e-demo on server https://192.168.42.218:8443

        http://watson-machine-learning-event-scorer-e2e-demo.192.168.42.218.nip.io (svc/watson-machine-learning-event-scorer)
          dc/watson-machine-learning-event-scorer deploys istag/watson-machine-learning-event-scorer:latest <-
            bc/watson-machine-learning-event-scorer source builds https://github.com/estherhi/cpd-quick-start-watson-machine-learning on openshift/python:3.6 
              build #1 running for 59 seconds - 14e1b33: iml git ignore (estherh <estherh@il.ibmcom>)
            deployment #1 waiting on image or update

        dc/container-event-producer deploys istag/container-event-producer:latest <-
          bc/container-event-producer source builds https://github.com/estherhi/cpd-quick-start-watson-machine-learning on openshift/python:3.6 
            build #1 running for 59 seconds - 14e1b33: iml git ignore (estherh <estherh@il.ibmcom>)
          deployment #1 waiting on image or update  
        
        
#### Custom Routing

An OpenShift route exposes a service at a host name, like www.example.com, so that external clients can reach it by name.

DNS resolution for a host name is handled separately from routing; you may wish to configure a cloud domain that will always correctly resolve to the OpenShift router, or if using an unrelated host name you may need to modify its DNS records independently to resolve to the router.

That aside, let's explore our new web app. `oc new-app` created a new route. To view your new route:

        $ oc get route

In the result you can find all routes in your project and for each route you can find its hostname.  
Find the `watson-assistant-quickstart` route and use the hostname to navigate to the newly created Node.js web app.
Notice that you can use the `APPLICATION_DOMAIN` template parameter to define a hostname for your app.

To create a new route at a host name, like www.example.com:

        $ oc expose svc/watson-assistant-quickstart --hostname=www.example.com


#### Optional diagnostics
        
If the build is not yet started (you can check by running `oc get builds`), start one and stream the logs with:

        $ oc start-build watson-assistant-quickstart --follow

Deployment happens automatically once the new application image is available.  To monitor its status either watch the web console or execute `oc get pods` to see when the pod is up.  Another helpful command is

        $ oc get svc
        
This will help indicate what IP address the service is running, the default port for it to deploy at is 8080. Output should look like:

        NAME                          CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
        watson-assistant-quickstart   172.30.249.251   <none>        8080/TCP   7m                


### Adding Webhooks and Making Code Changes
Assuming you used the URL of your own forked repository, you can configure your github repository to make a webhook call whenever you push your code. Learn more about [Webhook Triggers](https://docs.openshift.com/container-platform/3.5/dev_guide/builds/triggering_builds.html#webhook-triggers).

1. From the OpenShift web console homepage, navigate to your project
2. Go to Builds
3. Click the link with your BuildConfig name
4. Click the Configuration tab
5. Click the "Copy to clipboard" icon to the right of the "GitHub webhook URL" field
6. Navigate to your repository on GitHub and click on repository settings > webhooks > Add webhook
7. Paste your webhook URL provided by OpenShift
8. Leave the defaults for the remaining fields - That's it!
9. After you save your webhook, refresh your Github settings page and check the status to verify connectivity.  

### Learn more about [OpenShift templates](https://docs.openshift.com/enterprise/3.0/dev_guide/templates.html#dev-guide-templates).

### Known issues
1. Model versions supported in Watson Machine Learning are documented here - https://docs-icpdata.mybluemix.net/docs/content/SSQNUZ_current/com.ibm.icpdata.doc/dsx/models.html.
2. Each time the example is run a model is stored in Watson Machine Learning instance and a new deployment is generated.
3. The micro services are currently configured to accept insecure endpoints for Cloud Pak for Data. For production, use secure endpoints only.

## License
TBD
