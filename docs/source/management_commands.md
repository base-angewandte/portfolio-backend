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

- `year` - Year of the export.

##### Optional

- `--lang` - Label language of the export. Allowed values: `de` and `en`

### `import_bibtex`

This command imports all entries from a BibTeX file and creates according Portfolio
entries for a specific user.

```{note}
This is still an experimental feature, and implementation as well as mappings of
BibTeX types to Portfolio schemas might change in the future.
```

#### Arguments

##### Positional

- `userid` - the ID of the user for whom the imported entries should be created
- `file` - the full path to the BibTeX file to import entries from

#### Usage examples

A common usage might look like

```
python manage.py import_bibtex 12345ABCD67890EF12AB3456CD7890F0 references.bib
```

This assumes the `references.bib` file resides in the projects `src` directory.
But relative paths can be used as well. So in a local dev environment you might
want to use something like `~/Documents/references.bib`.

For a containerized setup, the easiest solution is to copy your file into the
`src` folder, and then execute the command via `docker-compose exec`:

```
docker-compose exec portfolio-django python manage.py import_bibtex 12345ABCD67890EF12AB3456CD7890F0 references.bib
```

### `push_to_showroom`

This command can be used to push single or bigger batches of entries to Showroom.
Only published entries will be pushed. After entries are pushed, their media and
their relations are also pushed. The success of the relations push depends on
whether the related entries are already available in Showroom (have been previously
pushed). In batch mode all entries are pushed before their media and relations are pushed.

#### Arguments

##### Positional

- `id` - the ID of a single entry to push (only used in case of not pushing `--all` (see options))

##### Optional

- `--all` - selects all published entries to be pushed (can be limited by the following options)
- `-l`, `--limit` - limits the actual amount of entries that are pushed in this batch. Default: None
- `-o`, `--offset` - number of entry in the whole set of entries to start from (0-indexed): Default: 0
- `-s`, `--status` - number of pushed entries after which a new status line should be printed. Default: None
- `-c`, `--cancel-threshold` - number of push errors after which to abort the whole operation. Default: 100

#### Usage examples

To push a single entry, use:

```shell
python manage.py push_to_showroom aBCde1fGHijKl2mnOPQr3t
```

Much more common will be a batch sync, pushing a few thousand entries, e.g. the first 10000,
while displaying some status output every 500 items:

```shell
python manage.py push_to_showroom --all --limit 10000 --offset 0 --status 500
```

Once this ran through you might continue with the next batch by increasing the limit to 10000.

In a containerized setup you can prepend the commands above with `docker-compose exec portfolio-django `
in order to start it from your host system (outside the container), as long as you are currently
in the root folder of the repository (e.g. `/opt/base/portfolio-backend/`).

```{note}
When you push a whole batch of entries (or even all at once), errors might occur for a single
or a few entries. In that case you will usually not want the whole batch sync to stop. But in
case a lot of errors happen (e.g. because the network connection went down) you might not want
the operation to continue, only to find out at the end, that almost all your entries could not
be pushed. Therefore, the management command will quit preemptively once 100 entries return
an error when their POST request was sent. This number can be adjusted with the `-c` or
`--cancel-threshold` option.

In case less then the cancel threshold errors happen with the POST requests for the entries,
the command will continue to push media and relations. Once in this stage, there is no extra
cancel threshold. So the management command will always try to complete these two stages and
list errors at the end.
```
