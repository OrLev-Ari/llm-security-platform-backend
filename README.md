
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `requirements.txt` file and rerun the `python -m pip install -r requirements.txt`
command.

## Deployment Prerequisites

### 1. Lambda Layer Dependencies

The Lambda functions use a layer for authentication dependencies (`bcrypt`, `PyJWT`). The layer is **automatically built during CDK synthesis** using Docker bundling - no manual steps required!

**How it works:**
- CDK automatically runs a Docker container during `cdk synth` or `cdk deploy`
- Dependencies from `lambda_layer/requirements.txt` are installed in a Linux environment
- The layer is packaged with the correct binaries for Lambda (Linux ARM64)

**Requirements:**
- Docker must be running (Docker Desktop on Windows)
- No manual build commands needed - CDK handles everything!

**Updating dependencies:**
1. Edit `lambda_layer/requirements.txt`
2. Run `cdk deploy` (CDK will rebuild the layer automatically)

### 2. Create JWT Secret in SSM Parameter Store

The authentication system requires a JWT secret stored in AWS Systems Manager Parameter Store:

```bash
aws ssm put-parameter \
  --name /llmplatformsecurity/jwtsecret \
  --value "your-strong-random-secret-key-here" \
  --type SecureString \
  --region us-east-1
```

**Generate a secure random secret:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Admin User Setup

The application uses JWT authentication with role-based authorization. Admin users have elevated privileges to create, update, and delete challenges.

### Creating the First Admin User

Admin users **cannot be created through the API** for security reasons. The first admin account must be manually inserted into the DynamoDB `UsersTable` using the AWS Console:

1. **Navigate to DynamoDB Console**
   - Go to AWS Console → DynamoDB → Tables
   - Select `UsersTable`

2. **Create Admin Item**
   - Click "Explore table items" → "Create item"
   - Switch to JSON view and insert:
   ```json
   {
     "username": "admin",
     "passwordHash": "$2b$12$YOUR_BCRYPT_HASH_HERE",
     "email": "admin@example.com",
     "country": "US",
     "dateOfBirth": "1990-01-01",
     "is_admin": true,
     "createdAt": 1713312000
   }
   ```

3. **Generate Password Hash**
   - Use Python to generate bcrypt hash:
   ```python
   import bcrypt
   password = "your-secure-password"
   hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   print(hash.decode('utf-8'))
   ```
   - Copy the output and replace `$2b$12$YOUR_BCRYPT_HASH_HERE` in the JSON above

4. **Important Notes**
   - Set `is_admin` to `true` (boolean, not string)
   - Use current Unix timestamp for `createdAt`
   - Username will be normalized to lowercase in the application
   - All regular users registered via `/auth/register` will have `is_admin: false`

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
