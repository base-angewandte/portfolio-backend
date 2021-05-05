# Management commands

Each command can be executed by running `docker-compose exec portfolio-django bash -c "python manage.py <command>"`
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
