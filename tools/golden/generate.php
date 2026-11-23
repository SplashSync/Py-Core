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
// Fields Definitions Fixtures
//====================================================================//
// Each case is a recipe: a list of FieldsFactory calls [method, ...args],
// replayed as is by the Python tests.

$fieldsRecipes = array(
    "simple" => array(
        array("create", "varchar", "name", "Name"),
        array("create", "text", "notes"),
        array("description", "  Some notes  "),
    ),
    "flags" => array(
        array("create", "varchar", "code", "Code"),
        array("isRequired"),
        array("isPrimary"),
        array("isIndexed"),
        array("isListed"),
        array("isLogged"),
        array("group", "General"),
        array("create", "int", "count", "Count"),
        array("isReadOnly"),
        array("isListHidden"),
        array("isNotTested"),
        array("create", "varchar", "secret", "Secret"),
        array("isWriteOnly"),
        array("create", "bool", "active", "Active"),
        array("isRequired", false),
        array("isReadOnly", false),
    ),
    "sync_modes" => array(
        array("create", "varchar", "a", "A"),
        array("setPreferRead"),
        array("create", "varchar", "b", "B"),
        array("setPreferWrite"),
        array("create", "varchar", "c", "C"),
        array("setPreferNone"),
        array("create", "varchar", "d", "D"),
        array("setPreferNone"),
        array("setPreferBoth"),
    ),
    "metadata" => array(
        array("create", "email", "email", "Email"),
        array("microData", "http://schema.org/ContactPoint", "email"),
        array("create", "phone", "phone", "Phone"),
        array("microData", "http://schema.org/PostalAddress", "telephone"),
        array("alternateMicroData", "http://schema.org/Person", "telephone"),
        array("alternateMicroData", "http://schema.org/PostalAddress", "telephone"),
        array("create", "url", "site", "Site"),
        array("microData", "http://schema.org/Organization", "url"),
        array("microData", "", "sameAs"),
    ),
    "choices_options" => array(
        array("create", "varchar", "status", "Status"),
        array("addChoices", array("draft" => "Draft", "done" => "  Done  ")),
        array("addChoice", "canceled", "Canceled"),
        array("addOption", "maxLength", 12),
        array("addOptions", array("isLowerCase" => true, "unit" => "kg")),
        array("create", "varchar", "firstname", "Firstname"),
        array("association", "firstname", "lastname", "firstname"),
    ),
    "lists" => array(
        array("create", "varchar", "sku", "SKU"),
        array("inList", "lines"),
        array("isReadOnly"),
        array("create", "double", "qty", "Quantity"),
        array("inList", "lines"),
        array("create", "objectid::Product", "product", "Product"),
        array("inList", "lines"),
        array("create", "price", "unit_price", "Unit Price"),
        array("inList", "lines"),
    ),
    "multilang" => array(
        array("setDefaultLanguage", "en_US"),
        array("create", "mvarchar", "title", "Title"),
        array("microData", "http://schema.org/Product", "name"),
        array("setMultiLang", "en_US"),
        array("create", "mvarchar", "title", "Title FR"),
        array("microData", "http://schema.org/Product", "name"),
        array("setMultiLang", "fr_FR"),
        array("create", "mtext", "desc", "Description ES"),
        array("setMultiLang", "es_ES"),
        array("create", "varchar", "not_ml", "Not ML"),
        array("setMultiLang", "fr_FR"),
        array("create", "mvarchar", "bad_iso", "Bad ISO"),
        array("setMultiLang", "xx"),
    ),
    "types" => array(
        array("create", "bool", "f_bool", "Bool"),
        array("create", "int", "f_int", "Int"),
        array("create", "double", "f_double", "Double"),
        array("create", "date", "f_date", "Date"),
        array("create", "datetime", "f_datetime", "Datetime"),
        array("create", "lang", "f_lang", "Lang"),
        array("create", "country", "f_country", "Country"),
        array("create", "state", "f_state", "State"),
        array("create", "currency", "f_currency", "Currency"),
        array("create", "price", "f_price", "Price"),
        array("create", "image", "f_image", "Image"),
        array("create", "file", "f_file", "File"),
        array("create", "inline", "f_inline", "Inline"),
        array("create", "objectid::ThirdParty", "f_parent", "Parent"),
    ),
    "template_apply" => array(
        array("create", "varchar", "civility"),
        array("template", "Splash.Templates.ThirdParty.Profile.CivilityType"),
        array("create", "varchar", "billing_zip", "Zip"),
        array("template", "Splash.Templates.Accounting.Billing.PostalCode"),
    ),
    "template_create" => array(
        array("createFromTemplate", "billing_name", "Splash.Templates.Accounting.Billing.Name"),
        array("createFromTemplate", "billing_alias", "Splash.Templates.Accounting.Billing.AlternateName", "Alias"),
        array("createFromTemplate", "admin_url", "Splash.Templates.Common.Links.AdminUrl"),
        array("createFromTemplate", "presence", "Splash.Templates.Common.Sync.Presence"),
        array("createFromTemplate", "country_name", "Splash.Templates.Accounting.Billing.CountryName"),
        array("createFromTemplate", "billing_address", "Splash.Templates.Accounting.Core.BillingAddress"),
    ),
    "template_lists" => array(
        array("createFromTemplate", "description", "Splash.Templates.Accounting.Items.Description"),
        array("inList", "lines"),
        array("createFromTemplate", "type", "Splash.Templates.Accounting.Items.Type"),
        array("inList", "lines"),
        array("create", "inline", "options"),
        array("inList", "lines"),
        array("template", "Splash.Templates.Accounting.Items.Options"),
    ),
    "template_overrides" => array(
        array("createFromTemplate", "civility", "Splash.Templates.ThirdParty.Profile.CivilityType"),
        array("isReadOnly"),
        array("name", "My Civility"),
        array("addChoice", "other", "Other"),
        array("createFromTemplate", "zip", "Splash.Templates.Accounting.Billing.PostalCode"),
        array("isRequired"),
        array("addOption", "maxLength", 5),
    ),
    "template_language" => array(
        array("setDefaultLanguage", "fr_FR"),
        array("createFromTemplate", "civility", "Splash.Templates.ThirdParty.Profile.CivilityType"),
        array("createFromTemplate", "billing_name", "Splash.Templates.Accounting.Billing.Name"),
    ),
    "invalid" => array(
        array("create", "varchar", "", "No Id"),
        array("create", "image", "picture", "Picture"),
        array("isPrimary"),
        array("create", "varchar", "ok", "Ok"),
        array("identifier", "renamed"),
        array("name", "Renamed"),
    ),
);

$fields = array();
foreach ($fieldsRecipes as $name => $recipe) {
    $factory = new \Splash\Core\Components\FieldsFactory();
    foreach ($recipe as $call) {
        $method = array_shift($call);
        $factory->{$method}(...$call);
    }
    $fields[] = array(
        "name" => $name,
        "recipe" => $fieldsRecipes[$name],
        "published" => $factory->publish(),
    );
}
//====================================================================//
// Templates used by recipes, exported in the catalog format
$templates = array();
foreach ($fieldsRecipes as $recipe) {
    foreach ($recipe as $call) {
        $code = match ($call[0]) {
            "template" => $call[1],
            "createFromTemplate" => $call[2],
            default => null,
        };
        $template = $code ? \Splash\Core\Helpers\FieldTemplatesHelper::resolve($code) : null;
        if (!$template || isset($templates[$code])) {
            continue;
        }
        $config = $template->getConfiguration("en_US");
        unset($config["name"], $config["desc"]);
        $names = $descriptions = array();
        foreach (array("en_US", "fr_FR", "it_IT", "es_ES", "de_DE") as $isoLang) {
            $names[$isoLang] = $template->getName($isoLang);
            $descriptions[$isoLang] = $template->getShortDescription($isoLang);
        }
        $templates[$code] = array(
            "code" => $code, "config" => $config, "name" => $names, "desc" => $descriptions,
        );
    }
}
writeFixture($target, "fields", array("cases" => $fields, "templates" => $templates));

//====================================================================//
// Widgets Fixtures
//====================================================================//

/**
 * Widget built from a recipe: identity, parameters and blocks factory calls.
 */
class GoldenWidget extends \Splash\Core\Models\AbstractWidget
{
    /**
     * Current widget recipe.
     */
    public static array $recipe = array();

    /**
     * Apply a recipe to widget static identity.
     */
    public static function configure(array $recipe): void
    {
        self::$recipe = $recipe;
        static::$name = $recipe["name"];
        static::$description = $recipe["description"];
        static::$ico = $recipe["icon"];
        static::$disabled = $recipe["disabled"];
        static::$options = $recipe["options"];
    }

    /**
     * {@inheritDoc}
     */
    public static function getType(): string
    {
        return "GoldenWidget";
    }

    /**
     * {@inheritDoc}
     */
    public function getParameters(): array
    {
        if (empty(self::$recipe["parameters"])) {
            return array();
        }
        foreach (self::$recipe["parameters"] as $call) {
            $method = array_shift($call);
            $this->fieldsFactory()->{$method}(...$call);
        }

        return $this->fieldsFactory()->publish();
    }

    /**
     * {@inheritDoc}
     */
    public function get(array $parameters = array()): ?array
    {
        $this->setTitle(static::$name);
        $this->setIcon(static::$ico);
        foreach (self::$recipe["blocks"] as $call) {
            $method = array_shift($call);
            self::blocksFactory()->{$method}(...$call);
        }
        $this->setBlocks(self::blocksFactory()->render() ?? array());

        return $this->render();
    }
}

$chartOptions = array("title" => "Sales", "xkey" => "day", "ykeys" => array("total"), "labels" => array("Total"));
$dataset = array(array("day" => "Mon", "total" => 12), array("day" => "Tue", "total" => 7.5));
$widgetsRecipes = array(
    "text" => array(
        array("addTextBlock", "Hello <b>World</b>"),
    ),
    "text_options" => array(
        array("addTextBlock", "Half", array("Width" => "col-xs-6", "AllowHtml" => true)),
    ),
    "set_data" => array(
        array("addTextBlock", "Text"),
        array("setData", "extra", "value"),
    ),
    "notifications" => array(
        array("addNotificationsBlock", array(
            "success" => "S", "info" => "I", "warning" => "W", "error" => "E", "other" => "ignored",
        )),
        array("addNotificationsBlock", array("info" => "Only info")),
    ),
    "table" => array(
        array("addTableBlock", array(array("Name", "Value"), array("Int", 12), array("Float", 2.5), array("Bool", true))),
    ),
    "spark_info" => array(
        array("addSparkInfoBlock", array(
            "title" => "Orders", "fa_icon" => "fa-cart", "value" => 42, "chart" => array(1, 2, 3), "extra" => "x",
        )),
    ),
    "morris" => array(
        array("addMorrisGraphBlock", $dataset, "Bar", $chartOptions),
        array("addMorrisGraphBlock", $dataset, "Area", array("xkey" => "day")),
        array("addMorrisGraphBlock", $dataset, "Line", $chartOptions, array("Width" => "col-xs-6", "AllowHtml" => false)),
    ),
    "morris_wrong_type" => array(
        array("addMorrisGraphBlock", $dataset, "Pie", $chartOptions),
    ),
    "morris_donut" => array(
        array("addMorrisDonutBlock", array(array("label" => "A", "value" => 1)), array("title" => "Donut", "xkey" => "x")),
    ),
);
$widgetsIdentities = array(
    "default" => array(
        "name" => "Golden", "description" => "Golden Widget", "icon" => "fa fa-info", "disabled" => false,
        "options" => array("Width" => \Splash\Core\Models\AbstractWidget::SIZE_DEFAULT), "parameters" => array(),
    ),
    "custom" => array(
        "name" => "Sales", "description" => "Last sales", "icon" => "fa fa-chart-line", "disabled" => true,
        "options" => array("Width" => \Splash\Core\Models\AbstractWidget::SIZE_XL, "Header" => true, "UseCache" => false),
        "parameters" => array(
            array("create", "int", "days", "Days"),
            array("create", "varchar", "mode", "Mode"),
            array("addChoices", array("day" => "Day", "week" => "Week")),
        ),
    ),
);

$widgets = array("descriptions" => array(), "renders" => array());
foreach ($widgetsIdentities as $name => $identity) {
    GoldenWidget::configure($identity + array("blocks" => array()));
    $description = (new GoldenWidget())->description();
    $widgets["descriptions"][] = array(
        "name" => $name,
        "identity" => $identity,
        "description" => $description,
        "xml" => xmlManager()->arrayToXml($description),
    );
}
foreach ($widgetsRecipes as $name => $recipe) {
    GoldenWidget::configure($widgetsIdentities["default"] + array("blocks" => $recipe));
    $render = (new GoldenWidget())->get();
    $widgets["renders"][] = array(
        "name" => $name,
        "recipe" => $recipe,
        "render" => $render,
        "xml" => xmlManager()->arrayToXml($render),
    );
}
writeFixture($target, "widgets", $widgets);

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
