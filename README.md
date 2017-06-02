# archiving-scheme

This is a Taurus scheme that provides access to the Tango archiving system.
It uses the [PyTangoArchiving](https://github.com/tango-controls/PyTangoArchiving)
module.

## Enabling
To enable it, install `archiving` and edit `<taurus>/tauruscustomsettings.py`
to add `archiving` to the `EXTRA_SCHEME_MODULES` list. For example:

```python
EXTRA_SCHEME_MODULES = ['archiving']
```

## Examples:

Once the new scheme is enabled in your taurus installation, you can:

- ... get the last 12h of `tdb` archived data from the tango attribute 
`a/b/c/d` with::

```python
import taurus
myattr = taurus.Attribute('archiving:/a/b/c/d?db=tdb?t0=-0.5d')
```
- Show the values in a TaurusForm:

```bash
$> taurusform 'archiving:/a/b/c/d?db=tdb?t0=-0.5d'
```
```
