Serverless
==========

This folder utilizes the `Serverless Framework <https://serverless.com/>`_ to deploy PhantomJS on an auto-scaling AWS Lambda function, so that your local machine does not need the compute power to render large pages at high velocity.

Setup
-----

Before you begin, make sure you have an AWS account and permissions to deploy CloudFormation stacks. This guide does not cover configuration of AWS IAM roles.

To set up the serverless framework, you need to install `Node <https://www.npmjs.com/>`_. Follow the official instructions `here <https://www.npmjs.com/get-npm>`_ to install npm on your local machine.

Next, we need to install Serverless. You can refer to the official `documentation <https://serverless.com/framework/docs/getting-started/>`_ for install instructions, however, it boils down to the following command.

::

    $ npm install -g serverless

Make sure to run this command in the ``/serverless`` folder you find this README in.

After we have serverless installed, we need to install one module to assist our deployment

::

    $ sls plugin install -n serverless-python-requirements

You are now ready to deploy your lambda function to do page renders.

Deployment
----------

This project primary consists of only a couple files that enable our success.

* ``serverless.yml`` - this is our template to upload into AWS. It configures the lambda function, the API Gateway, and the runtime configuration for everything.

* ``handler.py`` - this is our receiver for our API Gateway calls. It uses Phantom Snap to generate the render, and passes the data back to the caller

* ``requirements.txt`` - this file is a normal python requirements file that enables us to add additional packages to our lambda environment

To deploy or update our lambda function:

::

    $ sls deploy

If everything was successful, you should get the following output at the end:

::
    ...

    Service Information
    service: serverless-phantomjs
    stage: dev
    region: us-east-1
    stack: serverless-phantomjs-dev
    api keys:
      None
    endpoints:
      POST - https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/dev/render
    functions:
      render: serverless-phantomjs-dev-render

    ...

You will want to copy the POST endpoint, and use it in your ``LambdaRenderer`` configuration like so:

::

    config = {
        'url': 'https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/dev/render',
    }

    r = LambdaRenderer(config)


It is highly recommended you add authentication around your lambda function, otherwise anyone can use it. You can do this by modifying your ``serverless.yml`` file like so:

::

    ...
    provider:
      name: aws
      logRetentionInDays: 7
      runtime: python2.7
      apiKeys:
        - mySecretKey
    ...
          - http:
              method: post
              path: render
              private: true
    ...

When you deploy your serverless project, it will give you an api key like so:

::

    api keys:
      mySecretKey: ASHAJBFIUASHKBH1293612948

You can supply the resulting API key via the ``api_key`` configuration when you initialize the ``LambdaRenderer`` class.

Usage
-----

At this point, you should have a lambda function deployed, and we can use the same functional interface to render web pages.

::

    from phantom_snap.lambda_renderer import LambdaRenderer
    from phantom_snap.imagetools import save_image

    config = {
        'url': 'https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/dev/render',
        'api_key': 'ASHAJBFIUASHKBH1293612948',
    }

    r = LambdaRenderer(config)
    url = 'http://www.youtube.com'

    page = r.render(url, img_format='JPEG')
    save_image('/tmp/youtube-render', page)

    r.shutdown()

Cleanup
-------

When you no longer wish you use your lambda function, you can clean it up by doing:

::

    $ sls remove

And all your resources created in AWS will be removed.
