# Archival

Archive assets

## Add a new Archival System

To add a new archival system, you must build one and register it.

### Register an archival system

**TL;DR;**: You must register an archival class in the `media_server.archiver.factory.default.ArchiverFactory.mappings` `dict`,
with a key, that is defined in `media_server.archiver.factory.archives.Archives` and set the `ARCHIVE_TYPE`
environment variable to that key.

The archival system is registered in `media_server.archiver.factory.default.ArchiverFactory`.

`media_server.archiver.factory.default.ArchiverFactorymapping` contains a dictionary of all archival classes.
The keys are defined in`media_server.archiver.factory.archives.Archives`.
If the factory is not provided with a specified archival system in `media_server.archiver.factory.default.ArchiverFactory.create`
(as it is not in the current implementation in `media_server.archiver.controller.default.DefaultArchiveController`),
it will look up the key in the settings object `src/portfolio/settings` `ARCHIVE_TYPE` variable, which will take it from the environment variables.

### Create a new Archival System

**TL;DR;**: The archival class must inherit from `media_server.archiver.interface.abstractarchiver.AbstractArchiver`
and implement all abstract methods. Put it in the `media_server.archiver.implementations` module.

The following methods are called by `media_server.archiver.controller.default.DefaultArchiveController`

#### **init**()

Takes an `media_server.archiver.interface.archiveobject.ArchiveObject`-`dataclass` object as input,
which contains the `User`-object, the `Media`-objects and the `Entry` objects.

#### abstract method `validate`

Checks if the given input is valid for the archival target system. Raise `ValidationError` (with
the `throw_validation_errors` method), if the validation fails. It takes a dict as `{'fieldname': ['error_1', 'error_2'], }`
as input. Don't forget, that you need to give the portfolio field names as output, else the frontend and the user can
not handle the response.

#### abstract method `media_server.archiver.interface.abstractarchiver.AbstractArchiver.push_to_archive`

Pretty much, what it says: Push the information to the archive. Returns `SuccessfulArchiveResponse`.

#### abstract method `media_server.archiver.interface.abstractarchiver.AbstractArchiver.update_archive`

Pretty much, what it says: Update the information in the archive. Returns `SuccessfulArchiveResponse`.

## Existing Archival Systems

### Phaidra

`media_server.archiver.implementations.phaidra.main.PhaidraArchiver` is the entry point.

Phaidra archival consists of two parts: `Media`-objects (in
`media_server.archiver.implementations.phaidra.main.PhaidraArchiver.media_archiver`) and the corresponding `Entry`-object (in
`media_server.archiver.implementations.phaidra.main.PhaidraArchiver.metadata_data_archiver`).

They both work quite the same way: The have a translator-object, which inherits from
`media_server.archiver.implementations.phaidra.abstracts.datatranslation.AbstractDataTranslator` and
generates/translates the data from the `Entry`/`Media`-objects to the phaidra-format and a marshmallow-schema is used
for validation. The translator class also translates the errors from the phaidra-schema back to the portfolio-
datastructure, so the front-end/user can understand it.

There is one difference: The metadata of the Entry gets handled synchronously, the files asynchronously afterward.

#### Media Archival

`media_server.archiver.implementations.phaidra.media.archiver.MediaArchiveHandler` basically just passes the jobs to
`media_server.archiver.implementations.phaidra.media.archiver.MediaArchiver` with a redis queue.

#### Entry Archival

works the same way on normal entries, but gets somewhat tricky on thesis's, since some of the keys / properties of the
resulting json are dynamically set. In the database there are persons with roles – in rhe resulting json you find `role:<role-code>`
objects.

To achieve this, `media_server.archiver.implementations.phaidra.metadata.archiver.ThesisMetadataArchiver.concepts_mapper`
creates a `media_server.archiver.implementations.phaidra.metadata.mappings.contributormapping.BidirectionalConceptsMapper`,
that maps the portfolio-roles via skosmos to the phaidra-roles (which are from the library of congress).
This object is passed to
`media_server.archiver.implementations.phaidra.metadata.thesis.schemas.create_dynamic_phaidra_thesis_meta_data_schema`,
which enriches the marshmellow schema, which is a little tricky, because marshmallow (this is version 2 _cry_) uses a
lot of python's dynamic class stuff.
`media_server.archiver.implementations.phaidra.metadata.thesis.datatranslation.PhaidraThesisMetaDataTranslator` is easier,
since it only uses a dictionary internally and there is no need of dynamic class building.

#### Examples hypothetical changes

##### Add a new rule

Phaidra adds a new rule. All titles must be in title case.

This only concerns validation. Got to `media_server.archiver.implementations.phaidra.metadata.default.schemas.PhaidraContainer`.
(By the way, you do not have to change `media_server.archiver.implementations.phaidra.metadata.thesis.schemas.PhaidraThesisContainer`,
it inherits from the `PhaidraContainer`). There you would add a method with a `@validates`-devorator, like in
`media_server.archiver.implementations.phaidra.metadata.thesis.schemas.PhaidraThesisContainer.must_have_an_english_and_german_abstract`

You might want to add a test in `src/media_server/archiver/implementations/phaidra/phaidra_tests`. You must change the
existing functional tests, since validation will now fail on test-entries, which do not have title case.

##### Change the name of a field

The field `dcterms:language` in phaidra gets renamed to `schema:language`.

You have to:

- change the name in the data generation/translation
- change the name in the data validation
- change the name in tests

You find the top-level keys of the data translation here:
`media_server.archiver.implementations.phaidra.metadata.default.datatranslation.PhaidraMetaDataTranslator`. Just change
the key. This will apply to thesis as well, if the child class does not override the rule, which it does not.

You have to rename to fields load_from and dump_to arguments in the schema, which you do here:
`media_server.archiver.implementations.phaidra.metadata.thesis.schemas.PhaidraThesisContainer`

Finally, you have to rewrite the tests. Since they are not very structured, maybe just use file search and replace it.
