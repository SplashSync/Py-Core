<?php

/*
 *  This file is part of SplashSync Project.
 *
 *  Copyright (C) Splash Sync  <www.splashsync.com>
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 *
 *  For the full copyright and license information, please view the LICENSE
 *  file that was distributed with this source code.
 */

/**
 * Golden fixtures generator: produces reference wire data with the REAL Php-Core.
 *
 * Usage (from the repository root):
 *
 *   docker run --rm -v "$PWD:/py" -w /app --entrypoint php \
 *       splashsync/toolkit:3.0 /py/tools/golden/generate.php /py/tests/fixtures/golden
 */

require '/app/vendor/autoload.php';

use Splash\Core\Client\Splash;
use Splash\Core\Components\XmlManager;

//====================================================================//
// Settings
//====================================================================//

const WS_ID = "ThisIsSplashWsId";
const WS_KEY = "ThisIsYourEncryptionKeyForSplash";
const SOAP_URI = "http://toolkit.splashsync.local";

$target = $argv[1] ?? null;
if (!$target || !is_dir($target)) {
    fwrite(STDERR, "Usage: generate.php <target directory>\n");
    exit(1);
}

/**
 * Write a fixture file as pretty JSON.
 */
function writeFixture(string $target, string $name, array $contents): void
{
    $json = json_encode($contents, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION);
    file_put_contents($target."/".$name.".json", $json."\n");
}

/**
 * Get a fresh Php-Core Xml Manager.
 */
function xmlManager(): XmlManager
{
    return new XmlManager();
}

//====================================================================//
// Splash Configuration
//====================================================================//

$config = Splash::configuration();
$config->WsIdentifier = WS_ID;
$config->WsEncryptionKey = WS_KEY;

//====================================================================//
// XML Codec Fixtures
//====================================================================//

$payloads = array(
    "scalars" => array(
        "string" => "Hello World",
        "empty" => "",
        "int" => 42,
        "negative" => -7,
        "zero" => 0,
        "float" => 12.5,
        "float_integral" => 100.0,
        "float_rounding" => 0.1 + 0.2,
        "float_small" => 0.00001,
        "float_big" => 1e20,
        "float_long" => 123456789012345.678,
        "float_negative" => -0.75,
        "true" => true,
        "false" => false,
        "null" => null,
        "numeric_string" => "0012",
        "utf8" => "Été ☃ € 日本",
        "special" => "<a href=\"x\">&amp; 'quotes'</a>",
        "multiline" => "line1\nline2\r\n\ttabbed",
    ),
    "lists" => array(
        "strings" => array("a", "b", "c"),
        "ints" => array(1, 2, 3),
        "floats" => array(1.5, 2.0),
        "bools" => array(true, false),
        "nested" => array(array("x", "y"), array("k" => "v")),
        "empty_list" => array(),
        "sparse" => array(3 => "three", 7 => "seven"),
    ),
    "keys" => array(
        "field@list" => "at sign",
        "id::type" => "double colon",
        "dotted.key" => "dot",
        "with space" => "space",
        "dash-key" => "dash",
        "under_score" => "underscore",
        "CamelCase" => "camel",
        "12" => "numeric string key",
    ),
    "message" => array(
        "server" => array(
            "ServerType" => "PHP",
            "ProtocolVersion" => "1.2",
            "ServerHost" => "localhost",
        ),
        "service" => "Objects",
        "debug" => 0,
        "verbose" => 1,
        "tasks" => array(
            1 => array(
                "id" => 1,
                "name" => "Get",
                "desc" => "Read Object Data",
                "params" => array(
                    "type" => "ThirdParty",
                    "id" => "12",
                    "fields" => array("name", "email", "phone@lines"),
                ),
            ),
        ),
        "taskscount" => 1,
        "log" => array(
            "err" => array(),
            "war" => array("A warning"),
            "msg" => array("Message 1", "Message 2"),
            "deb" => array(),
        ),
    ),
);

$codec = array();
foreach ($payloads as $name => $payload) {
    $xml = xmlManager()->arrayToXml($payload);
    $codec[] = array(
        "name" => $name,
        "payload" => $payload,
        "xml" => $xml,
        "decoded" => xmlManager()->xmlToArray($xml),
    );
}
writeFixture($target, "codec", array("cases" => $codec));

//====================================================================//
// AES Cipher Fixtures
//====================================================================//

$ws = Splash::ws();
$crypt = new ReflectionMethod($ws, 'crypt');
$cipherCases = array(
    array(WS_KEY, WS_ID, "<SPLASH>x</SPLASH>"),
    array(WS_KEY, WS_ID, str_repeat("0123456789abcdef", 4)),
    array(WS_KEY, WS_ID, "Été ☃ € 日本"),
    array("AnotherKey", "AnotherId", str_repeat("Lorem ipsum dolor sit amet. ", 40)),
    array("k", "i", "a"),
);
$cipher = array();
foreach ($cipherCases as list($key, $wsId, $plain)) {
    $encrypted = $crypt->invoke($ws, 'encrypt', $plain, $key, $wsId);
    $cipher[] = array(
        "key" => $key,
        "id" => $wsId,
        "plain" => $plain,
        "cipher" => $encrypted,
        "roundtrip" => $crypt->invoke($ws, 'decrypt', $encrypted, $key, $wsId),
    );
}
writeFixture($target, "cipher", array("cases" => $cipher));

//====================================================================//
// Full Messages (pack) Fixtures
//====================================================================//

$ws->setup();
//====================================================================//
// Php-Core shares one XMLWriter: only the first message of a process carries
// the XML declaration. Warm it up so every fixture reflects the steady state.
$ws->pack(array("warmup" => true));
$messages = array();
foreach (array("scalars", "message") as $name) {
    $messages[] = array(
        "name" => $name,
        "key" => WS_KEY,
        "id" => WS_ID,
        "payload" => $payloads[$name],
        "encrypted" => $ws->pack($payloads[$name]),
        "unsecured" => $ws->pack($payloads[$name], true),
    );
}
writeFixture($target, "messages", array("cases" => $messages));

//====================================================================//
// SOAP Envelopes Fixtures
//====================================================================//

/**
 * PHP SoapClient that captures requests instead of sending them.
 */
class CaptureSoapClient extends SoapClient
{
    public array $requests = array();

    public ?string $nextResponse = null;

    /**
     * Capture the request and return a canned response.
     */
    public function __doRequest(
        string $request,
        string $location,
        string $action,
        int $version,
        bool $oneWay = false,
        ?string $uriParserClass = null
    ): ?string {
        $this->requests[] = array("location" => $location, "action" => $action, "body" => $request);

        return $this->nextResponse;
    }
}

//====================================================================//
// Server side functions, as registered by Php-Core SOAPInterface
foreach (array("Ping", "Connect", "Admin", "Objects", "Files", "Widgets") as $service) {
    eval(sprintf(
        'function %s($id = null, $data = null) { return "RESPONSE-%s-".$id."-".$data; }',
        $service,
        $service
    ));
}

/**
 * Run a PHP SoapServer on a raw request and capture the output.
 */
function soapServerHandle(string $request): string
{
    $server = new SoapServer(null, array("uri" => SOAP_URI));
    foreach (array("Ping", "Connect", "Admin", "Objects", "Files", "Widgets") as $service) {
        $server->addFunction($service);
    }
    ob_start();
    $server->handle($request);

    return (string) ob_get_clean();
}

$client = new CaptureSoapClient(null, array(
    "location" => "http://python.splashpy.local/splash",
    "uri" => SOAP_URI,
    "exceptions" => false,
));
$soap = array("php_client" => array(), "php_server" => array());
foreach (array("Ping", "Connect", "Objects") as $service) {
    $client->requests = array();
    $client->__soapCall($service, array("id" => WS_ID, "data" => "Q29udGVudA=="));
    $request = $client->requests[0];
    $soap["php_client"][] = array(
        "service" => $service,
        "params" => array("id" => WS_ID, "data" => "Q29udGVudA=="),
        "location" => $request["location"],
        "action" => $request["action"],
        "request" => $request["body"],
    );
    $soap["php_server"][] = array(
        "service" => $service,
        "request" => $request["body"],
        "response" => soapServerHandle($request["body"]),
    );
}
//====================================================================//
// Client decoding of a server response
$client->nextResponse = $soap["php_server"][0]["response"];
$soap["php_client_decode"] = array(
    "response" => $client->nextResponse,
    "decoded" => $client->__soapCall("Ping", array("id" => WS_ID, "data" => "Q29udGVudA==")),
);
//====================================================================//
// PHP SoapServer fault: SoapServer::fault() terminates the script,
// so the fixture is written from a shutdown function.
//====================================================================//

register_shutdown_function(static function () use ($target, $soap): void {
    $soap["php_server_fault"] = (string) ob_get_clean();
    writeFixture($target, "soap", $soap);
    echo "Golden fixtures written to ".$target."\n";
});
ob_start();
(new SoapServer(null, array("uri" => SOAP_URI)))->fault("Server", "SOAP call: service died unexpectedly!!");
