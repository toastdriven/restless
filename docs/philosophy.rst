.. _philosophy:

==========================
Philosophy Behind Restless
==========================

Quite simply, I care about creating flexible & RESTFul APIs. In building
Tastypie, I tried to create something extremely complete & comprehensive.
The result was writing a lot of hook methods (for easy extensibility) & a lot
of (perceived) bloat, as I tried to accommodate for everything people might
want/need in a flexible/overridable manner.

But in reality, all I really ever personally want are the RESTful verbs, JSON
serialization & the ability of override behavior.

This one is written for me, but maybe it's useful to you.

.. note:

    I wrote most of Tastypie & have worked with many other RESTful frameworks.
    Commentary here is not meant as a slam, simply a point of difference.


Pithy Statements
================

Keep it **simple**
    Complexity is the devil. It makes it harder to maintain, hard to be
    portable & hard for users to work with.

Python 3 is the default
    Why write for the past? We'll support it, but Python 2.X should be treated
    as a (well-supported) afterthought.

BSD Licensed
    Any other license is a bug.

Work with as many web frameworks as possible.
    Django is my main target, but I want portable code that I can use from
    other frameworks. Switching frameworks ought to be simply a change of
    inheritance.

RESTful by default
    REST is native to the web & works well. We should make it easy to *be*
    RESTful.

    If I wanted RPC, I'd just write my own crazy methods that did whatever I
    wanted.

JSON-only
    Because XML sucks, bplist is Apple-specific & YAML is a security rats nest.
    Everything (I care about) speaks JSON, so let's keep it simple.

B.Y.O.D. (Bring Your Own Data)
    Don't integrate with a specific ORM. Don't mandate a specific access format.
    We expose 8-ish simple methods (that map cleanly to the REST
    verbs/endpoints). Data access/manipulation happens there & the user knows
    best, so they should implement it.

No HATEOAS
    I loved HATEOAS dearly, but it is complex & making it work with many
    frameworks is a windmill I don't care to tilt at. Most people never use
    the deep links anyhow.

No Authorization
    Authorization schemes vary so wildly & everyone wants something different.
    Give them the ability to write it without natively trying to support it.
