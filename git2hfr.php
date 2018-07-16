/*****************************/
/* Licence : Apache 2        */
/* Auteur : roger21          */
/* But : autoupdate post hfr */
/*****************************/

<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>GitHub 2 HFR</title>
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

$posts=[
  [
    "source" => "https://raw.githubusercontent.com/XaaT/hfr-toulouse/master/post-1.txt",
    "formulaire" => "https://forum.hardware.fr/message.php?config=hfr.inc&cat=13&post=89952&numreponse=19682010&page=1&p=1&subcat=431&sondage=0&owntopic=2#formulaire",
    ],
  [
    "source" => "https://raw.githubusercontent.com/XaaT/hfr-toulouse/master/post-2.txt",
    "formulaire" => "https://forum.hardware.fr/message.php?config=hfr.inc&cat=13&post=92651&numreponse=23723254&page=1&p=1&subcat=427&sondage=0&owntopic=0#formulaire",
    ],
  ];

// les cookies
$cookies="md_user=roger21; md_passs=";



/********************************************/
/* début de la boucle sur tous les messages */
/********************************************/

foreach($posts as $post){

  $source=$post["source"];
  $formulaire=$post["formulaire"];



/******************************/
/* récupération du formulaire */
/******************************/

  $context=stream_context_create(["http" => ["method" => "GET", "header" => "Cookie: ".$cookies."\r\n"]]);
  $page=file_get_contents($formulaire, false, $context);
  $dom=new DOMDocument();
  @$dom->loadHTML($page);
  $xpath=new DOMXPath($dom);
  $form=$xpath->query("//form[@name=\"hop\" and @id=\"hop\"]");
  $form=$form->item(0);



/**************************************************************/
/* récupération et construction des champs du formaulaire hfr */
/**************************************************************/

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
  $data["content_form"] = file_get_contents($source);



/********************/
/* l'envoie du post */
/********************/

  $url="https://forum.hardware.fr/bdd.php?config=hfr.inc";
  $context=stream_context_create(["http" => ["method" => "POST",
                                             "header" => "Content-type: application/x-www-form-urlencoded\r\nCookie: ".$cookies."\r\n",
                                             "content" => http_build_query($data)]]);
  $result=file_get_contents($url, false, $context);



/****************************************/
/* affichage de qqchose pour faire joli */
/****************************************/

  $dom=new DOMDocument();
  @$dom->loadHTML($result);
  $xpath=new DOMXPath($dom);
  $div=$xpath->query("//div[@class=\"hop\"]/text()");
  $result=$div->item(0)->nodeValue;
  echo($result)."<br>";



/******************************************/
/* fin de la boucle sur tous les messages */
/******************************************/

}

?>
</body>
</html>
