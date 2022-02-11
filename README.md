[![Python 2.7 3.7](https://img.shields.io/badge/python-2.6%20%7C%202.7%20%7C%203.7-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Documentation
This repository is a part of the ShotGrid Pipeline Toolkit.

- For more information about this app and for release notes, *see the wiki section*.
- For general information and documentation, click here: https://developer.shotgridsoftware.com/d587be80/?title=Integrations+User+Guide
- For information about ShotGrid in general, click here: http://www.shotgridsoftware.com/toolkit

## Using this app in your Setup
All the apps that are part of our standard app suite are pushed to our App Store.
This is where you typically go if you want to install an app into a project you are
working on. For an overview of all the Apps and Engines in the Toolkit App Store,
click here: https://developer.shotgridsoftware.com/.

## Have a Question?
Don't hesitate to contact us! You can find us on https://developer.shotgridsoftware.com/


## Changes in this fork.

- Extracted behavior determining which Entity media should be uploaded to into a hook.
- Configurable through the context_selector_hook and entity_parent_fields settings.
- The default context_selector_hook strips version numbers off the ends of sequences and tries to match the name against the shotgun_entity_type setting as well as Sequence and Shot entities.
- If a match is not found, a dialog is shown to allow users to select or create an Entity to upload to.

This enables flame artists to Duplicate a sequence and add a version name onto the end, without resulting in tk-flame-review creating a new Sequence in ShotGrid every time. Instead, the media will be uploaded as a Version for the original Sequence.

<p float="left">
  <img src="/resources/context_selector_Select.png" width="260" />
  <img src="/resources/context_selector_NewSequence.png" width="260" /> 
  <img src="/resources/context_selector_NewShot.png" width="260" />
</p>
