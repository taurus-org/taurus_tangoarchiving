# taurus_tangoarchiving

This is a Taurus scheme that provides access to the Tango archiving system.
It uses the [PyTangoArchiving](https://github.com/tango-controls/PyTangoArchiving)
module. 

This module also provide a programmatic taurusgui: `tpgarchiving`. This GUI requires [taurus_pyqtgraph](https://github.com/taurus-org/taurus_pyqtgraph) plugin.
The GUI defines 3 main widgets: A tpg `TaurusPlot`, a `TangoArchivingModelSelectorItem` and a pg `LegendItem`. These widgets allows to choose any archiving attributes and plot it.

## Enabling
This plugin is auto register and  auto enabling during the installation.

## Install 
You can install it via `python setup.py install` or `pip install .`

## Examples:

Once the new scheme is enabled in your taurus installation, you can use `tpgarch` URIS with taurus.

e.g.

- Get the last 12h of `tdb` archived data from the tango attribute
`a/b/c/d` with::

```python
import taurus
myattr = taurus.Attribute('tgarch:/a/b/c/d?db=tdb?t0=-0.5d')
```

**NOTE**: More URIS examples can be found on the `test.test_tangoarchivingvalidator.py`
module of this project.

- Show the values in a TaurusForm:

```bash
$> taurusform 'tgarch:/a/b/c/d?db=tdb?t0=-0.5d'
```

- Or simplilly run the `tpgarchiving` taurusgui:

```bash
$> tpgarchiving
```

