#
<!-- badges: start -->

[![lifecycle](https://img.shields.io/badge/lifecycle-active-orange.svg)](https://www.tidyverse.org/lifecycle/#active)

[![NSF-1948926](https://img.shields.io/badge/NSF-1948926-blue.svg)](https://www.nsf.gov/awardsearch/showAward?AWD_ID=1948926)

<!-- badges: end -->

## Working with the Python Data Upload Template

This set of python scripts is intended to support the bulk upload of a set of records to Neotoma. It consists of three key steps:

1. Development of a data template (YAML and CSV)
2. Template validation
3. Data upload

Once these three steps are completed the uploader will push the template files to the `neotomaholding` database. This is a temporary database that is intended to hold data within the Neotoma Paleoecology Database system for access by Tilia. Tilia is then used to provide a final data check and upload of data to Neotoma proper.

![The process of uploading records using the bulk uploader. Individuals follow the steps outlined above and described further in this README file.](img/BulkUploaderSchema.svg)

## Template Development

The template uses a `yaml` format file, with the following general structure for each data element:

```yaml
apiVersion: neotoma v2.0
kind: Development
metadata:
  - column:  Site.name
    neotoma: ndb.sites.sitename  
    vocab: False
    repeat: True
    type: string
    ordered: False
```

The template is used to link the template CSV file (the file that will be generated by the upload team) to the Neotoma database. It is a form of cross-walk between the upload team and the existing database structure.

All YAML files should begin with an `apiVersion` header that indicates we are using `neotoma v2.0`. This is the current API version for Neotoma (accessible through [api.neotomadb.org](https://api.neotomadb.org)). This field is intended to support future development of the Neotoma API.

The `kind` field indicates whether we are prepared to work with the production version of the database. Options are `development` and `production`. For testing purposes all YAML files should set `kind` to `development`.

## `metadata`

Each entry in the `metadata` tab can have the following entries:

* `column`:  The column of the spreadsheet that is being described.
* `neotoma`: A database table and column combination from the database schema.
* `vocab`: If there is a fixed vocabulary for the column, include the possible terms here.
* `repeat`: [`true`, `false`] Is each entry unique and tied to the row (`false`, this isn't a set of repeated values), or is this a set of entries associated with the site (`true`, there is only a single value that repeats throughout)?
* `type`: [`integer`, `numeric`, `date`] The variable type for the field.
* `ordered`: [`true`, `false`] Does the order of the column matter?

```yaml
metadata:
  - column: Coordinate.precision
    neotoma: ndb.collectionunits.location
    vocab: ['core-site','GPS','core-site approximate','lake center']
    repeat: True
    type: character
    ordered: False
```

In this case we see that the team has chosen to create a column in their spreadsheet called `Coordinate.precision`, it is linked to the Neotoma table/column `ndb.collectionunits.location`. We state that it requires one term from a fixed vocabulary, the value repeats within the column, it is expected to be a `character` (as opposed to an `integer` or `numeric` value) and the order of the values does not matter.

A complete list of Neotoma tables and columns is included in [`tablecolumns.csv`](docs/tablecolumns.csv), and additional support for table concepts and content can be found either in the [Neotoma Paleoecology Database Manual](https://open.neotomadb.org/manual) or in the [online database schema](https://open.neotomadb.org/dbschema).

Using the YAML template we can create complex relationships between existing data models for particular sets of records coming from individual researcher labs or data consortiums and the Neotoma database.

On completion of the YAML file, each column of the CSV will have an entry that fully describes the content of the data within that column. At that point we can validate the CSV files intended for upload.

## Validation

We execute the validation process by running:

```bash
> python3 template_validate.py FILEFOLDER
```

This will then search the folder provided in `FILEFOLDER` for csv files and parse them for validity.

The set of tests for validity depends on the data content within the YAML file, but must at least include:

* Site Validation
* Collection Unit Validation
* Analysis Unit Validation
* Dataset Validation
* Dataset PI Validation
* Sample Validation
* Data Validation

Templates with more elements will be tested depending on the data content provided.

Each file will recieve a `log` file associated with it that contains a report of potential issues:

```txt
53f0a3feb956a4fa590a9d45b657f76e
Validating data/FILENAME.csv
Report for data/FILENAME.csv
=== Checking Template Unit Definitions ===
✔ All units validate.
. . .
. . .
=== Checking the Dating Horizon is Valid ===
✔  The dating horizon is in the reported depths.
```

The log files begin with an [md5 hash](https://en.wikipedia.org/wiki/MD5) of the csv template file. This appears as a string of numbers and letters that record a point in time of the file. The hash is used to identify whether or not files have changed since validation.

The validation step identifies each element of the template being validated, provides a visual reference as to whether or not the element passes validation (**✔**, **?** or **✗**) and provides guidance as to whether changes need to be made.

## Upload

The upload process is initiated using the command:

```bash
> python3 template_upload.py
```

The upload process will return the distince siteids, and related data identifiers for the uploads.
