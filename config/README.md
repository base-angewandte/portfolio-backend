# base project config

A repository containing some base config settings for our base projects.

These are usually included as a git subtree in a project repository.
See for reference the `update-config-default` rule in the `base.mk` file.

## Usage in project repos

The individual config files (e.g. `.isort.cfg` or `.hadolint`) are then
linked to in the project repo's root directory.

Only the `.pre-commit-config.yaml`
should be copied, as every project might use different tags for the python
version.

Also, the `.gitinore` usually should be created with the `make gitignore`
command, rather than linking it, to also include project specific ignores,
which should be put into a `.gitignore.local` file in your project repo
root directory. As long as you don't have project specific ignores you can
also just link to the `.gitignore` in the included config subtree.
