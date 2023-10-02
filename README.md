# polygon-zone

Proof of concept for polygon zones in Home Assistant.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

<img width="980" alt="Zrzut ekranu 2023-10-02 085400" src="https://github.com/Baael/polygon-zone/assets/38595/d9de9c49-3155-4856-ad80-8208b4f68527">



Whipped up quickly, so it needs optimization, refactoring, cleaning up, and possibly a complete rewrite from scratch.

It's based on using [shapely](https://pypi.org/project/shapely)

I'll try to upload the editor based on [@geoman-io/leaflet-geoman-free](https://www.npmjs.com/package/@geoman-io/leaflet-geoman-free) when I get some free time.

In short:

 - I created a new class called `polygon_zone` that inherits from zone.
 - I added an attribute named `points`.
 - If the zone has points, then it’s a `polygon_zone` otherwise I use the old class, so I don’t have issues with backward compatibility.
 - I determine the center of the zone and its area.
 - In the `_init_.py` file, in the in_zone method, I check if the instance has the `points` attribute. If it does, I check if the tracker’s `point` is within the polygon using `polygon.contains(point)`. This is on lines 97 to 104.
 - Otherwise, I check if the point is within the radius, like for normal zone.
