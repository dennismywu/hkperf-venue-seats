# Publishing the project page

The project page lives at https://code.denniswu.org/hkperf-venue-seats/: `site/index.html`, a public
copy of the viewer (`app/`) under `viewer/`, and the seat lists under `data/`.

## Build

```bash
deploy/build.sh
```

This writes `dist/hkperf-venue-seats/` (git-ignored). To preview it, serve `dist/` and open
http://localhost:8771/hkperf-venue-seats/.

## One-time server set-up (Apache on the DigitalOcean droplet)

1. DNS: add an `A` record for `code.denniswu.org` pointing at the droplet (the same address as
   `denniswu.org`).
2. On the server, as a sudo user:

   ```bash
   sudo mkdir -p /var/www/code.denniswu.org/public/hkperf-venue-seats
   sudo chown -R "$USER": /var/www/code.denniswu.org
   sudo cp code.denniswu.org.conf /etc/apache2/sites-available/
   sudo a2enmod headers
   sudo a2ensite code.denniswu.org
   sudo apachectl configtest && sudo systemctl reload apache2
   sudo certbot --apache -d code.denniswu.org
   ```

   The first `cp` assumes `deploy/code.denniswu.org.conf` has been copied to the server.

## Publish

```bash
DEPLOY_HOST=user@code.denniswu.org deploy/publish.sh
```

It builds, then copies `dist/hkperf-venue-seats/` to `/var/www/code.denniswu.org/public/hkperf-venue-seats/`
with rsync (`DEPLOY_PATH` overrides the path).

## Links back to the repository

`app/config.js` holds the repository URL used for every "source data" link on the page and in the
viewer. Revise it when the repository moves or goes public; the links 404 for the public while it is
private.
