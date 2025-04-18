# Serverless Application

## Overview
This is a serverless application built using [AWS Lambda](https://aws.amazon.com/lambda/), [API Gateway](https://aws.amazon.com/api-gateway/), [DynamoDB](https://aws.amazon.com/dynamodb/), and [AWS Step Functions](https://aws.amazon.com/step-functions/). It provides a scalable and cost-effective solution for handling backend logic, data storage, and workflow orchestration.

## Features
- Serverless architecture
- RESTful API endpoints
- DynamoDB integration for data persistence
- Step Function for workflow orchestration
- Easy deployment with AWS CDK
- Unit testing support
- Environment-based logging configuration

## Prerequisites
- [Node.js](https://nodejs.org/) (v20 or later)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [AWS CDK](https://aws.amazon.com/cdk/) installed globally

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/serverless-application.git
   cd serverless-application
   ```

2. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Bootstrap your AWS environment for CDK:
   ```bash
   cdk bootstrap
   ```

## Deployment
1. Deploy the application using AWS CDK:
   ```bash
   cdk deploy --all
   ```

2. Note the API Gateway endpoint URL and Step Function ARN from the deployment output.

## Usage
- Use tools like [Postman](https://www.postman.com/) or `curl` to interact with the API.
- Example request:
  ```bash
  curl -X POST https://your-api-endpoint/user -d '{"id": "1", "name": "John Doe"}' -H "Content-Type: application/json"
  ```

- **Step Function**:
  - The Step Function orchestrates multiple requests in parallel.
  - Example input for the Step Function:
    ```json
    {
      "requests": [
        {
          "resource": "/users",
          "httpMethod": "GET"
        },
        {
          "resource": "/user",
          "httpMethod": "POST",
          "body": "{\"id\":\"1\",\"name\":\"John Doe\"}"
        }
      ]
    }
    ```

## Project Structure
```
/serverless_application
  /src
    /events       # Example event payloads for testing
    main.py       # Lambda function entry point
  /tests
    /unit         # Unit tests
  app.py          # CDK app entry point
  serverless_application_stack.py # CDK stack definition
```

### Key Files
- **`app.py`**: Entry point for the AWS CDK application.
- **`serverless_application_stack.py`**: Defines the infrastructure, including Lambda, API Gateway, DynamoDB, and Step Functions.
- **`/src/main.py`**: Contains the Lambda function logic.
- **`/src/events`**: Example event payloads for testing the application.
- **`/tests/unit`**: Unit tests for the application.

## Testing
1. Run unit tests:
   ```bash
   pytest tests/unit
   ```

## CI/CD
- The project includes GitHub Actions workflows for continuous integration and deployment.
- Workflows :

[![Deploy CDK App](https://github.com/SaiJitendraKalli/ServerlessApplication/actions/workflows/deploy-cdk-app.yml/badge.svg?event=workflow_dispatch)](https://github.com/SaiJitendraKalli/ServerlessApplication/actions/workflows/deploy-cdk-app.yml)   
## License
This project is licensed under the MIT License.
