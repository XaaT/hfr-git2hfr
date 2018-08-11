<?php

/*


Copyright 2018 XaTriX

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


https://github.com/XaaT/hfr-git2hfr/


*/

?><!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Git 2 HFR</title>
</head>
<body>
<?php



ini_set("display_errors", "1");
ini_set("error_reporting", "-1");
ini_set("html_errors", "1");



/******************/
/* les paramètres */
/******************/


// les messages à actualiser

//   source -> le contenu du message (le raw de github)
//   formulaire -> la page d'edition du message
//   (optionnel) message -> le contenu (en BBCode) du message de signalement de la mise à jour

$posts=[
  [
    "source" => "https://raw.githubusercontent.com/XaaT/hfr-toulouse/master/post-1.txt",
    "formulaire" => "https://forum.hardware.fr/message.php?config=hfr.inc&cat=13&post=89952&numreponse=19682010&page=1&p=1&subcat=431&sondage=0&owntopic=2#formulaire",
    "message" => "pouet",
  ],
  [
    "source" => "https://raw.githubusercontent.com/XaaT/hfr-toulouse/master/post-2.txt",
    "formulaire" => "https://forum.hardware.fr/message.php?config=hfr.inc&cat=13&post=92651&numreponse=23723254&page=1&p=1&subcat=427&sondage=0&owntopic=0#formulaire",
    "message" => "pouet pouet

COMMIT_MESSAGE

prout prout

caca caca",
  ],
];


// les cookies

$cookies="md_user=roger21; md_passs=";


// la clé de sécurisation (le content-type du webkook doit être application/json)

$key="";



/***********************************************/
/* fonction de vérification de la sécurisation */
/***********************************************/


function secured(&$commit_message=""){
  global $key, $talktome;
  if(!$key){
    $talktome.="<br>\npas de clé de sécurisation<br>\n<br>\n";
    return true;
  }
  if(!isset($_SERVER["HTTP_X_HUB_SIGNATURE"]) ||
     strpos($_SERVER["HTTP_X_HUB_SIGNATURE"], "sha1=") !== 0){
    $talktome.="<br>\npas de signature<br>\n<br>\n";
    return false;
  }
  list($algo, $signature)=explode("=", $_SERVER["HTTP_X_HUB_SIGNATURE"]);
  $content=file_get_contents("php://input");
  $content_array=json_decode($content, true);
  //$talktome.="<br>\n<pre>".var_export($content_array, true)."</pre><br>\n<br>\n";
  if(isset($content_array["head_commit"]["message"])){
    $commit_message=$content_array["head_commit"]["message"];
  }
  //$talktome.="<br>\n<pre>".var_export($commit_message, true)."</pre><br>\n<br>\n";
  $hash=hash_hmac($algo, $content, $key);
  if(hash_equals($signature, $hash)){
    $talktome.="<br>\nsécurisation ok<br>\n<br>\n";
    return true;
  }else{
    $talktome.="<br>\nsécurisation caca<br>\n<br>\n";
    return false;
  }
}



/***********************/
/* fonction de postage */
/***********************/


function postage($formulaire, $source, $new=false){

  // récupération du formulaire de postage

  global $cookies, $talktome;
  $context=stream_context_create(["http" => ["method" => "GET", "header" => "Cookie: ".$cookies."\r\n"]]);
  $page=file_get_contents($formulaire, false, $context);
  $dom=new DOMDocument();
  @$dom->loadHTML($page);
  $xpath=new DOMXPath($dom);
  $form=$xpath->query("//form[@name=\"hop\" and @id=\"hop\"]");
  $form=$form->item(0);

  // récupération et construction des champs du formaulaire

  $data=[];

  // les inputs
  $inputs1=$xpath->query(".//input[not(@type=\"checkbox\" or @type=\"radio\") and @name and @value]", $form);
  $inputs2=$xpath->query(".//input[(@type=\"checkbox\" or @type=\"radio\") and @name and @value and @checked=\"checked\"]", $form);
  foreach([$inputs1, $inputs2] as $inputs){
    foreach($inputs as $input){
      $name=$input->attributes->getNamedItem("name")->nodeValue;
      $value=$input->attributes->getNamedItem("value")->nodeValue;
      $data[$name]=$value;
    }
  }

  // les selects
  $selects=$xpath->query(".//select[@name]", $form);
  foreach($selects as $select){
    $name=$select->attributes->getNamedItem("name")->nodeValue;
    $options=$xpath->query(".//option[@value and @selected=\"selected\"]", $select);
    if($options->length > 0){
      $value=$options->item(0)->attributes->getNamedItem("value")->nodeValue;
      $data[$name]=$value;
    }
  }

  // le message
  $data["content_form"] = $source;

  // envoie du formulaire

  $url="https://forum.hardware.fr/bdd.php?config=hfr.inc";
  if($new){
    $url="https://forum.hardware.fr/bddpost.php?config=hfr.inc";
  }
  $context=stream_context_create(["http" => ["method" => "POST",
                                             "header" => "Content-type: application/x-www-form-urlencoded\r\nCookie: ".$cookies."\r\n",
                                             "content" => http_build_query($data)]]);
  $result=file_get_contents($url, false, $context);

  // récupération de la réponse

  $dom=new DOMDocument();
  @$dom->loadHTML($result);
  $xpath=new DOMXPath($dom);
  $div=$xpath->query("//div[@class=\"hop\"]/text()");
  $result=trim($div->item(0)->nodeValue);
  //$talktome.="<pre>".var_export($data, true)."</pre><br>\n";
  $talktome.=$result."<br>\n";

}



/*************************************/
/* boucle de traitement des messages */
/*************************************/


$talktome="";
if(secured($commit_message)){
  foreach($posts as $post){
    $source=file_get_contents($post["source"]);
    $formulaire=$post["formulaire"];
    postage($formulaire, $source);
    if(isset($post["message"]) && !empty($post["message"]) && !empty(trim($post["message"]))){
      $source=str_replace("COMMIT_MESSAGE", $commit_message, trim($post["message"]));
      $formulaire=preg_replace("/&numreponse=[0-9]+/", "", str_replace("#formulaire", "", $formulaire))."&new=0";
      //$talktome.="$formulaire<br>\n";
      postage($formulaire, $source, true);
    }
  }
}



/****************************************/
/* affichage de qqchose pour faire joli */
/****************************************/


echo $talktome;



?>
</body>
</html>
