# Authors

## Software

**Ori Amos**: software design and implementation of PoCo / Polony Review. This covers the local web app
(backend in `src/polony_app`, React frontend in `frontend/`), the one-command installers in `install/`, and the tests.

Ori Amos holds the copyright (see [LICENSE](LICENSE)).

## Scientific context

The counting method is solid-phase single-molecule PCR (polony PCR, Mitra & Church, 1999). It was adapted at the
Lindell lab, Technion, to quantify marine viruses of a given clade in field samples. See the
[README](README.md#authors-acknowledgements-and-citation).

## Scientific collaborators

TODO (Ori): list the scientific collaborators here, with the name and role of each person. Only add names that have
been checked with the people concerned. Until this section is filled in, no individuals are named in this project.

## Upstream work

The file-format conventions for the historical ImageJ-annotated TIFFs (embedded ROI and Overlays blobs, counter
positions, counting-grid lines, and the file naming scheme) were learned from the lab's files and from the earlier
counting scripts at [kirill-push/polony-counting](https://github.com/kirill-push/polony-counting) (MIT licence).

No code was copied from that project. The import code in `src/polony_app/legacy_import` is new code.
See [ATTRIBUTION.md](src/polony_app/legacy_import/ATTRIBUTION.md) and [NOTICE](NOTICE).

## Contributors

The git history of this repository starts with a single import of the earlier work, followed by commits made in assisted
sessions. The commit author names in this repository therefore do **not** show who wrote the code. Authorship is as stated in
this file and in [NOTICE](NOTICE). The earlier history stays in the original repository,
[oriamos/polony-counting](https://github.com/oriamos/polony-counting), which is kept for reference.

Future contributors are recorded in the git history and in the pull requests of this repository.
