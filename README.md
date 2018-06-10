# sap

sap is a tool for *S*ynchronizing *A*rbitrary *P*ackages between
two or more systems.

sap is a simple method of sharing source code libraries between microservices,
fetching credential files (like Google's service account `credentials.json`),
or any other files.

## How It Works

1. A package containing some files is created and placed on your private server.
2. The package is then installed via `sap save package-name` wherever the files are needed.

## Examples

### Sharing Source Code

Project `bar` depends on libraries maintained in project `foo`'s git repository.

1. From the `foo`'s get repository, create your package.
    * `sap source add foo-libs libs/ -p "**.py"`
    * This will find all files in `libs/` that match `**.py` (`**` is the convention for recursive matching) and place them in a package file called `foo-libs-0.0.1.zip` on your sap server.
2. When working in the `bar` project, fetch the latest `foo-libs` package.
    * `sap save foo-libs`
    * If `foo-libs` is not installed, or an older version, this will pull the most recent `foo-libs` from your sap server and install them in `foo-libs/`.
3. Add to your deployment pipeline. For example, in your Dockerfile:
    * `RUN pip install sap && (cd /app/bar && sap install foo-libs)`
    * This installs sap in your container and fetches the latest foo-libs package.

