// Static snapshot based on OONI measurements for Vietnam (2026-06-01 to
// 2026-07-29). An OONI anomaly is not always proof of blocking, so this list
// intentionally excludes gambling, adult, torrent, and inactive sites.
// Add another root domain here when a useful site also needs WARP.
const warpDomains = [
    // Academic and standards
    "ieee.org",
    "ieee802.org",

    // Technology and communities
    "medium.com",
    "pastebin.com",
    "xda-developers.com",
    "linktr.ee",
    "mstdn.jp",
    "minds.com",

    // International news
    "bbc.com",
    "bbc.co.uk",
    "rfi.fr",
    "haaretz.com",
    "taz.de",

    // Social networks and communication
    "reddit.com",
    "redd.it",
    "redditstatic.com",
    "redditmedia.com",
    "telegram.org",
    "t.me",

    // Digital rights and human rights
    "amnesty.org",
    "freespeechdebate.com",
    "secfirst.org",
    "the88project.org",
    "vnwhr.net",
    "vnhrnet.org",

    // Vietnamese-language news
    "baotiengdan.com",
    "danquyen.com",
    "luatkhoa.com",
    "thoibao.com",
    "vietbao.com",
    "vietinfo.eu",
    "vietnamthoibao.org",
    "vietnamvoice.org",
    "viettan.org",
    "nguoi-viet.com",
    "sbtn.tv",
];

function FindProxyForURL(url, host) {
    host = host.toLowerCase();

    for (let i = 0; i < warpDomains.length; i++) {
        const domain = warpDomains[i];
        if (host === domain || dnsDomainIs(host, "." + domain)) {
            return "SOCKS5 127.0.0.1:40000";
        }
    }

    return "DIRECT";
}
