# sap

![sap header image](sap-800x200.png?raw=true)

sap is a tool for *S*ynchronizing *A*rbitrary *P*ackages between
two or more systems.

sap is a simple method of sharing source code libraries between microservices,
fetching credential files (like Google's service account `credentials.json`),
or any other files.

## How It Works

1. A package containing some files is created and placed on your private server.
2. The package is then installed via `sap install package-name` wherever the files are needed.

## Examples

### Sharing Source Code

Project `bar` depends on libraries maintained in project `foo`'s git repository.

1. From `foo`'s git repository, create your package.
    * `sap source add foo-libs libs/ -p "**.py"`
    * This will find all files in `libs/` that match `**.py` (`**` is the convention for recursive matching) and uploads them in a package file called `foo-libs-0.0.1.zip` on your sap server.
2. When working in the `bar` project, fetch the latest `foo-libs` package.
    * `sap install foo-libs`
    * If `foo-libs` is not installed, or an older version, this will pull the most recent `foo-libs` from your sap server and install them in `foo-libs/`.
    * If `--save` is specified, this will write changes to a `sap.json` in the CWD (or elsewhere with `-f`).
3. Add to your deployment pipeline. For example, in your Dockerfile:
    * `RUN pip install sap && (cd /app/bar && sap -y install)`
    * This installs sap in your container and fetches any packages defined in the `sap.json` file. The `-y` is equivalent to Apt's `-y`.

