---
title: "Corona Inzidenz"
date: 2021-05-13
author: "Dennis"
categories: ["Corona"]
image: CoronaInzidenzThumbnail.jpg
---

# Corona Inzidenz

Corona is a widely spread topic at the moment. It changed many people’s lives and the everyday life. At our school and generally in most of Germany a specific integer decides how we are allowed to live. It is called Inzidenz in German and calculated per city by getting the amount of infected people over the course of seven days for every 100,000 citizens in that city. Sounds complicated? It is. The data used for this calculation comes from the RKI. They have a website which shows all the statistics on infections in Germany and its cities. In the backend lies a database with all the infections and dates. It worked really well at first, showing different kinds of diagrams to inspect the course of Corona, but the more data was put into the database the slower the website got. It takes me on average more than 30 seconds on the computer to navigate to the incidence of the city I live in, and it took me almost two minutes to do the same thing on my phone.

The website is just too slow.

So I figured I should scrape the data from the original site and put it on my own site, resulting in load times of only a few milliseconds.

I first needed to figure out where I could get my data from. The original website uses an ArcGIS map with an SQL server in the backend. The following link leads to the backend API:

[https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?f=json&where=%28BL%3D%27Niedersachsen%27%29+AND+%28county+LIKE+%27%25Goslar%25%27%29&outFields=%2A&returnGeometry=false](https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?f=json&where=%28BL%3D%27Niedersachsen%27%29+AND+%28county+LIKE+%27%25Goslar%25%27%29&outFields=%2A&returnGeometry=false)

The link can be split into 6 parts:

1. `https://services7.arcgis.com/`
    - The standard link towards an ArcGIS map
2. `mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query`
    - The map ID and some server information
3. `?f=json`
    - The type of file that should be returned. This can be HTML or JSON though JSON has a faster load time.
4. `&where=%28BL%3D%27Niedersachsen%27%29+AND+%28county+LIKE+%27%25Goslar%25%27%29`
    - Translating to `&where=(BL='Niedersachsen') AND (county LIKE '%Goslar%')`
    - A good eye might have noticed the SQL pattern already. It tells the server to look for the state, in this case Niedersachsen and the city, in this case Goslar.
5. `&outFields=%2A`
    - Translating to `&outFields=*` Just means that the link should return every element in the SQL column.
6. `&returnGeometry=false`
    - I am not entirely sure what this is about, but it is needed to prevent loads of unnecessary data to be downloaded.

By replacing the `*` with `cases7_per_100k` the only value returned is the incidence that I want to scrape. With a bit of JavaScript I managed to download the JSON data and get the desired value.

```javascript
const jsonUrl = ...//the link I talked about earlier
//Get Inzidenz
getJSON(jsonUrl, function(data) {
     const containsValue = (data.features.length == 1);
     var inzidenz = "Fehler";
     if (containsValue) {
          inzidenz = data.features[0].attributes.cases7_per_100k;
          inzidenz = (String)((inzidenz*1000).toFixed()/1000).replace('.', ',');
     };
     const svgTextElement = document.getElementById("Inzidenz");
     svgTextElement.innerHTML = inzidenz;
});
```

For my example the JSON looks like this:

```json
{
     "objectIdFieldName": "OBJECTID",
     "uniqueIdField": {
          "name": "OBJECTID",
          "isSystemMaintained": true
     },
     "globalIdFieldName": "",
     "geometryType": "esriGeometryPolygon",
     "spatialReference": {
          "wkid": 25832,
          "latestWkid": 25832
     },
     "fields": [
          {
                "name": "cases7_per_100k",
                "type": "esriFieldTypeDouble",
                "alias": "Fälle letzte 7 Tage/100.000 EW",
                "sqlType": "sqlTypeOther",
                "domain": null,
                "defaultValue": null
          }
     ],
     "features": [
          {
                "attributes": {
                     "cases7_per_100k": 41.8219704751563
                }
          }
     ]
}
```

While the important part is the `features - attributes - cases7_per_100k` attribute. This value is the one that gets displayed on my website. If you clicked on any of the links to my website you may have realized the arguments that are passed. `Bundesland` is used to determine the state and `Kreis` is used to set the city.
