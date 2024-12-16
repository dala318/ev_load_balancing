# Integration architecture

Might be an overstatement to call it a design but anyway the code is split in 5 major parts

* **The coordinator**: [coordinator.py](custom_components/ev_load_balancing/coordinator.py) is what runs in the background and keeps track of inputs, calculates the new limits and set the limit of charging.
* **Service entities**: [sensor.py](custom_components/ev_load_balancing/sensor.py) that provides some live data from the state of balancing. These are only a facade to the coordinator which hold the actual data.
* **Mains consumption**: [mains/](custom_components/ev_load_balancing/mains/) active load on mains phases. They are instances of the base class [Mains](custom_components/ev_load_balancing/mains/__init__.py#L31) which shall define all methods and properties that are called from the coordinator. 
* **Charger settings**: [chargers/](custom_components/ev_load_balancing/chargers/) interface to set limits on the charger. They are instances of the base class [Charger](custom_components/ev_load_balancing/chargers/__init__.py#L35) which shall define all methods and properties that are called from the coordinator. 
* **Configuration editor**: [config_flow.py](custom_components/ev_load_balancing/config_flow.py) used only during set-up and re-configure and defines the settings the integration shall use. It does to some extent instantiate the Mains and Charger classes to retrieve the device specific properties but only temporary, after completion those are discarded and only string-values are stored in the config_entry.

# Adding new integration support

For every new supported device-type or integration there are some tasks to be done

* If a new integration dependency is added, make sure to add it in the `after_dependencies` section in [manifest.json](custom_components/ev_load_balancing/manifest.json), this makes it more likely that the initialization of service is successful on first attempt after reboot.
* Add new instance for mains or charger in respective folder that inherits from either base-class.
* Add necessary `CONF_` constants in [const.py](custom_components/ev_load_balancing/const.py) and import in necessary files.
* Update the `get_mains` or `get_charger` function in coordinator.py to enable selection of that type.
* Update the necessary steps and lists in `config_flow.py` to allow configuration of the new source/destination. (This step may require some refactoring since the variations are not known and not all steps are that general, even special device-specific steps may be required, then those should likely be imported from the device-specific file.)
* If the framework is not sufficiently supporting the new integration or device, create a request for update and we will solve it.
* If the config_entry is no longer backwards compatible add a migration function in [async_migrate_entry](custom_components/ev_load_balancing/__init__.py#L58) function and modify the VERSION and MINOR_VERSION accordingly in `config_flow.py`
* _Likely a lot more steps that I have not thought of yet..._
