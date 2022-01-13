# Management commands

Each command can be executed by running `docker-compose exec portfolio-django python manage.py <command>`
or if running the project locally by executing `python manage.py <command>` in `src`.

## Available Commands

### `clear_entries`

This command deletes all entries from Portfolio.

```{warning}
This action is not reversible.
```

### `export_published`

This command exports published entries for a specific year as CSV. Exported CSV files can be found in `src/export`.

#### Arguments

##### Positional

* `year` - Year of the export.

##### Optional

* `--lang` - Label language of the export. Allowed values: `de` and `en`


### `import_bibtex`

This command imports all entries from a BibTeX file and creates according Portfolio
entries for a specific user.

Note, that this is still a beta feature, and implementation as well as mappings of
BibTeX types to Portfolio schemas might change in the future.

#### Arguments

##### Positional

* `userid` - the ID of the user for whom the imported entries should be created
* `file` - the full path to the BibTeX file to import entries from


#### Usage examples

A common usage might look like

```
python manage.py import_bibtex 12345ABCD67890EF12AB3456CD7890F0 references.bib
```

This assumes the `references.bib` file resides in the projects `src` directory.
But relative paths can be used as well. So in a local dev environment you might
want to use something like `~/Documents/references.bib`.

For a containerized setup, the easiest soultion is to copy your file into the
`src` folder, and then execute a bash inside the django container:

```
sudo docker exec -it portfolio-django bash
```

Then inside the container the common usage example from above should work fine.
