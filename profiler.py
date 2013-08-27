"""
Profiler
==============

A basic profiler to measure performance
and identify bottlenecks.
"""

import cProfile, pstats
import brain
from digester.wikidigester import WikiDigester
from adipose import Adipose

def profile_wikidigester():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages', db='test')
    w.purge()

    print('Profiling WikiDigester...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)


def profile_wikidigester_distrib():
    # Create a WikiDigester
    w = WikiDigester('data/wiki/wiki_profile.xml', 'pages', distrib=True, db='test')
    w.purge()

    print('Profiling WikiDigester distributed...')

    p = cProfile.Profile()
    p.runctx('w.digest()', None, {'w': w})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)


def profile_bag_of_words():
    doc = 'Anarchism as a mass [[social movement]] has regularly endured fluctuations in popularity. The central tendency of anarchism as a social movement has been represented by [[Anarchist communism|anarcho-communism]] and [[anarcho-syndicalism]], with [[individualist anarchism]] being primarily a literary phenomenon&lt;ref&gt;[[Alexandre Skirda|Skirda, Alexandre]]. \'\'Facing the Enemy: A History of Anarchist Organization from Proudhon to May 1968\'\'. AK Press, 2002, p. 191.&lt;/ref&gt; which nevertheless did have an impact on the bigger currents&lt;ref&gt;Catalan historian Xavier Diez reports that the Spanish individualist anarchist press was widely read by members of [[anarcho-communist]] groups and by members of the [[anarcho-syndicalist]] trade union [[Confederación Nacional del Trabajo|CNT]]. There were also the cases of prominent individualist anarchists such as [[Federico Urales]] and [[Miguel Gimenez Igualada]] who were members of the [[Confederación Nacional del Trabajo|CNT]] and J. Elizalde who was a founding member and first secretary of the [[Iberian Anarchist Federation]]. Xavier Diez. \'\'El anarquismo individualista en España: 1923–1938.\'\' ISBN 978-84-96044-87-6&lt;/ref&gt; and individualists have also participated in large anarchist organizations.&lt;ref&gt;&lt;!--The exact location of this excerpt should be added to the reference.--&gt;{{cite web |url=http://public.federation-anarchiste.org/IMG/pdf/Cedric_Guerin_Histoire_du_mvt_libertaire_1950_1970.pdf |title=Pensée et action des anarchistes en France: 1950–1970 |last=Guérin |first=Cédric |page= |pages= |at= |language=French |archiveurl=http://web.archive.org/web/20070930014916/http://public.federation-anarchiste.org/IMG/pdf/Cedric_Guerin_Histoire_du_mvt_libertaire_1950_1970.pdf |archivedate=30 September 2007 |deadurl=yes |quote=Within the [[Synthesis anarchism|synthesist]] anarchist organization, the [[Fédération Anarchiste]], there existed an individualist anarchist tendency alongside anarcho-communist and anarchosyndicalist currents. Individualist anarchists participating inside the [[Fédération Anarchiste]] included [[Charles-Auguste Bontemps]], Georges Vincey and André Arru.}}&lt;/ref&gt;&lt;ref&gt;In Italy in 1945, during the Founding Congress of the [[Italian Anarchist Federation]], there was a group of individualist anarchists led by Cesare Zaccaria who was an important anarchist of the time.[http://www.katesharpleylibrary.net/73n6nh Cesare Zaccaria (19 August 1897-October 1961) by Pier Carlo Masini and Paul Sharkey]&lt;/ref&gt; Many anarchists [[non-aggression principle|oppose all forms of aggression]], supporting [[self-defense]] or [[non-violence]] ([[anarcho-pacifism]]),&lt;ref name=&quot;ppu.org.uk&quot;&gt;{{cite web |url=http://www.ppu.org.uk/e_publications/dd-trad8.html#anarch%20and%20violence |title=&quot;Resisting the Nation State, the pacifist and anarchist tradition&quot; by Geoffrey Ostergaard'

    print('Profiling bag of words...')

    p = cProfile.Profile()
    p.runctx('brain.bag_of_words(doc)', {'doc': doc}, {'brain': brain})
    ps = pstats.Stats(p)

    # See which specific func takes the most time.
    ps.sort_stats('time').print_stats(10)


if __name__ == '__main__':
    profile_wikidigester()
    profile_wikidigester_distrib()
    profile_bag_of_words()
