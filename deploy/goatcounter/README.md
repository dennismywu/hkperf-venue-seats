# Usage statistics: self-hosted GoatCounter

The viewer, the planner (after its consent screen) and the project page count page views and named
interface events (for example `viewer-venue-<id>`, which venue the viewer shows, and
`planner-category-added`) with GoatCounter running on the droplet at https://stats.denniswu.org/. GoatCounter
sets no cookies and keeps no IP addresses; the pages never send anything a visitor types or selects apart
from the venue shown. `app/analytics.js` does nothing until `goatcounter` is set in `app/config.js`.

## One-time set-up (on the droplet, as root)

1. DNS: add `stats.denniswu.org` (CNAME to `denniswu.org`, like `code`).
2. Install GoatCounter (check https://github.com/arp242/goatcounter/releases for the current version):

   ```bash
   V=v2.7.0
   curl -fsSL -o /tmp/gc.gz "https://github.com/arp242/goatcounter/releases/download/$V/goatcounter-$V-linux-amd64.gz"
   gunzip -c /tmp/gc.gz > /usr/local/bin/goatcounter && chmod 755 /usr/local/bin/goatcounter
   useradd --system --home /var/lib/goatcounter --create-home --shell /usr/sbin/nologin goatcounter
   ```

3. Create the site and your login (it asks for a password):

   ```bash
   sudo -u goatcounter /usr/local/bin/goatcounter db create site -createdb \
     -db=sqlite+/var/lib/goatcounter/goatcounter.sqlite3 \
     -vhost=stats.denniswu.org -user.email=YOU@EXAMPLE.COM
   ```

4. Service and web server (copy `goatcounter.service` and `stats.denniswu.org.conf` to the server first):

   ```bash
   cp goatcounter.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now goatcounter
   cp stats.denniswu.org.conf /etc/apache2/sites-available/
   a2enmod proxy proxy_http headers && a2ensite stats.denniswu.org
   apachectl configtest && systemctl reload apache2
   certbot --apache -d stats.denniswu.org --redirect
   ```

5. Sign in at https://stats.denniswu.org/ and, under Settings → Data collection, keep only what is needed
   (for example turn off Referrer and Region; keep Sessions, Screen size and Country, or fewer).
6. Point the pages at it: set `goatcounter: "https://stats.denniswu.org/count"` in `app/config.js`,
   commit, and publish (`deploy/publish.sh`). The Content-Security-Policy in `code.denniswu.org.conf`
   already allows this host; copy the updated file to the server and reload Apache.

Flags change between GoatCounter versions; `goatcounter help serve` and `goatcounter help db` show the
ones for the installed version.
