# stir

![stir header image](stir-800x200.png?raw=true)

stir is a tool for *S*ynchronizing *A*rbitrary *P*ackages between
two or more systems.

stir is a simple method of sharing source code libraries between microservices,
fetching credential files (like Google's service account `credentials.json`),
or any other files.

## How It Works

1. A package containing some files is created and placed on your private server.
2. The package is then installed via `stir install package-name` wherever the files are needed.

## Examples

### Sharing Source Code

Project `bar` depends on libraries maintained in project `foo`'s git repository.

1. From `foo`'s git repository, in a directory that will be the package root, create your package.
    * `stir upsert foolibs -p "**.py"`
    * This will find all files in the current that match `**.py` (`**` is the convention for recursive matching).
2. From `foo`'s git repository, run `stir publish foolibs`. This will bundle the package (`foolibs-0.0.1.zip`) and push it to the server.
3. When working in the `bar` project, fetch the latest `foolibs` package.
    * `stir install foolibs`
    * If `foolibs` is not installed, or an older version, this will pull the most recent `foolibs` package from your stir server and install it in `foolibs/`.
4. Add to your deployment pipeline. For example, in your Dockerfile:
    * `RUN pip install stir && (cd /app/bar && stir -y install foolibs)`
