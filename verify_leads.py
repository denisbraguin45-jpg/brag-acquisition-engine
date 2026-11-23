import json

NEW_DENIS_LEADS = [
    {"name": "Regatta Yachts São Paulo", "ig": "regattayachts", "wa": "5511957997972", "city": "São Paulo", "state": "SP", "slug": "regatta-yachts-sp", "bio": "Maior dealer náutico do Brasil. Concessionária oficial Schaefer Yachts, Sea-Doo e barcos premium."},
    {"name": "Regatta Yachts Guarujá", "ig": "regattayachts", "wa": "5511984470016", "city": "Guarujá", "state": "SP", "slug": "regatta-yachts-guaruja", "bio": "Showroom náutico e marina no Iate Clube de Santos Guarujá. Embarcações novas e seminovos certificados."},
    {"name": "Regatta Yachts Ilhabela", "ig": "regattayachts", "wa": "5511982065019", "city": "Ilhabela", "state": "SP", "slug": "regatta-yachts-ilhabela", "bio": "Base náutica Ilhabela. Venda de iates, lanchas e assistência técnica autorizada."},
    {"name": "WS Náutica Curitiba & BC", "ig": "wsnautica", "wa": "5541984112713", "city": "Curitiba", "state": "PR", "slug": "ws-nautica-curitiba", "bio": "Concessionária Focker, Mercury Marine e Sea-Doo no Paraná e Santa Catarina. Showrooms em Curitiba e Balneário."},
    {"name": "FF Motorsports Floripa", "ig": "ffmotorsportsbr", "wa": "5548999343939", "city": "Florianópolis", "state": "SC", "slug": "ff-motorsports-floripa", "bio": "Concessionária autorizada BRP Sea-Doo, Can-Am e lanchas Focker em Florianópolis."},
    {"name": "NautiCLASS Intermediações", "ig": "nauticlass", "wa": "5548991724533", "city": "Florianópolis", "state": "SC", "slug": "nauticlass-florianopolis", "bio": "Boutique náutica especializada em compra, venda e assessoria de iates e lanchas de luxo em SC."},
    {"name": "Sessa Marine Brasil", "ig": "sessamarinebrasil", "wa": "554832499983", "city": "Palhoça", "state": "SC", "slug": "sessa-marine-intech-boating", "bio": "Estaleiro e concessionária oficial dos iates italianos Sessa Marine no Brasil por Intech Boating."},
    {"name": "Azimut Yachts Brasil", "ig": "azimutyachts_brasil", "wa": "551333484000", "city": "Itajaí", "state": "SC", "slug": "azimut-yachts-brasil", "bio": "Líder mundial na fabricação de iates de luxo a motor. Concessionárias e marinas exclusivas no Brasil."},
    {"name": "Schaefer Yachts Floripa", "ig": "schaeferyachts", "wa": "554821060001", "city": "Florianópolis", "state": "SC", "slug": "schaefer-yachts-floripa", "bio": "Maior estaleiro de iates do Brasil. Showroom matriz de lanchas e yachts de 30 a 85 pés."},
    {"name": "Expert Yachts Schaefer SP", "ig": "expertyachts", "wa": "5511984470016", "city": "São Paulo", "state": "SP", "slug": "expert-yachts-schaefer-sp", "bio": "Concessionária autorizada Schaefer Yachts na capital paulista e litoral."},
    {"name": "FBA Náutica Recife", "ig": "fbanautica", "wa": "5581971195431", "city": "Recife", "state": "PE", "slug": "fba-nautica-recife", "bio": "Concessionária autorizada NX Boats e motores Mercury Marine para o Nordeste."},
    {"name": "Marina Tahiti BRP Bauru", "ig": "marinatahiti", "wa": "5514997009229", "city": "Bauru", "state": "SP", "slug": "marina-tahiti-bauru-brp", "bio": "Concessionária BRP Sea-Doo, Can-Am e marina completa no interior paulista."},
    {"name": "Villa Motorsports Campinas", "ig": "villamotorsports", "wa": "551932387375", "city": "Campinas", "state": "SP", "slug": "villa-motorsports-campinas-brp", "bio": "Concessionária BRP oficial Sea-Doo, Can-Am e Spyder em Campinas e região."},
    {"name": "Rio Náutica Prudente", "ig": "rionauticapp", "wa": "551839280077", "city": "Presidente Prudente", "state": "SP", "slug": "rio-nautica-prudente", "bio": "Concessionária autorizada Sea-Doo, lanchas Fibrafort Focker e motores Yamaha."},
    {"name": "Oeste Marine Náutica", "ig": "oestemarine", "wa": "5518997110022", "city": "Presidente Prudente", "state": "SP", "slug": "oeste-marine-prudente", "bio": "Concessionária de barcos Levefort, lanchas Focker e motores Mercury na Alta Sorocabana."},
    {"name": "Sea Náutica Rio Preto", "ig": "seanautica", "wa": "5517997120033", "city": "São José do Rio Preto", "state": "SP", "slug": "sea-nautica-rio-preto", "bio": "Concessionária e marina de barcos, lanchas e jet skis novos e seminovos em Rio Preto."},
    {"name": "Náutica Prime Piracicaba", "ig": "nauticaprime", "wa": "5519996861212", "city": "Piracicaba", "state": "SP", "slug": "nautica-prime-piracicaba", "bio": "Multimarcas náutica premium. Venda de lanchas, jet skis e carretas no interior de SP."},
    {"name": "Boreal Powersports Campo Grande", "ig": "borealpowersports", "wa": "556730468282", "city": "Campo Grande", "state": "MS", "slug": "boreal-powersports-campo-grande", "bio": "Concessionária BRP Sea-Doo e Can-Am no Mato Grosso do Sul."},
    {"name": "Dismoto Náutica Campo Grande", "ig": "dismotonautica", "wa": "5567981700067", "city": "Campo Grande", "state": "MS", "slug": "dismoto-nautica-campo-grande", "bio": "Concessionária náutica autorizada Yamaha Náutica e barcos de alumínio no MS."},
    {"name": "Villa Motorsports Cuiabá", "ig": "villamotorsportscuiaba", "wa": "5565996496262", "city": "Cuiabá", "state": "MT", "slug": "villa-motorsports-cuiaba", "bio": "Concessionária BRP Sea-Doo e Can-Am no Mato Grosso. Linha completa de jet skis e quadriciclos."},
    {"name": "Disnáutica Várzea Grande", "ig": "disnautica", "wa": "5565984416571", "city": "Várzea Grande", "state": "MT", "slug": "disnautica-varzea-grande", "bio": "Concessionária de barcos, lanchas e motores de popa Mercury no Mato Grosso."},
    {"name": "Náutica X Cuiabá", "ig": "nauticaxcuiaba", "wa": "5565999812420", "city": "Cuiabá", "state": "MT", "slug": "nautica-x-cuiaba", "bio": "Concessionária exclusiva Fishing Raptor e Mercury Marine para o Centro-Oeste."},
    {"name": "Jet Tech BRP Manaus", "ig": "jettechmanaus", "wa": "559236523900", "city": "Manaus", "state": "AM", "slug": "jet-tech-manaus-brp", "bio": "Concessionária oficial BRP Sea-Doo, Evinrude e lanchas Ventura no Amazonas."},
    {"name": "Marreco de Goiás Barcos", "ig": "marrecodebarcos", "wa": "5562996358587", "city": "Goiânia", "state": "GO", "slug": "marreco-de-goias-barcos", "bio": "Fabricante e concessionária de embarcações de alumínio e lazer náutico em Goiás."},
    {"name": "Center Náutica Goiânia", "ig": "centernauticagyn", "wa": "556232052200", "city": "Goiânia", "state": "GO", "slug": "center-nautica-goiania", "bio": "Concessionária autorizada Levefort, motores Mercury e acessórios náuticos em GO."},
    {"name": "Barcos Fisher Goiânia", "ig": "barcosfisher", "wa": "556232230606", "city": "Goiânia", "state": "GO", "slug": "barcos-fisher-goiania", "bio": "Venda e representação de barcos, lanchas e motores de popa em Goiânia."},
    {"name": "RM Náutica Itajaí", "ig": "rmnauticaoficial", "wa": "5547992869590", "city": "Itajaí", "state": "SC", "slug": "rm-nautica-itajai", "bio": "Suporte, comércio de seminovos e assistência autorizada Focker e Yamaha em Itajaí."},
    {"name": "Fibrafort Estaleiro Matriz", "ig": "fibrafortboats", "wa": "5547996585643", "city": "Itajaí", "state": "SC", "slug": "fibrafort-estaleiro-focker", "bio": "Maior fabricante de lanchas da América Latina (Linha Focker de 18 a 42 pés). Showroom de fábrica."},
    {"name": "Da Fonte Náutica Recife", "ig": "dafontenautica", "wa": "558133251022", "city": "Recife", "state": "PE", "slug": "d-fonte-nautica-imbiribeira", "bio": "Concessionária BRP Sea-Doo e Can-Am líder no Nordeste há mais de 30 anos."},
    {"name": "Chiquinho Náutica Nordeste", "ig": "chiquinhonauticape", "wa": "5581995144000", "city": "Recife", "state": "PE", "slug": "chiquinho-nautica-nordeste", "bio": "Concessionária multimarcas náutica em Pernambuco. Lanchas, jet skis e quadriciclos novos e seminovos."}
]

print("Count of new leads:", len(NEW_DENIS_LEADS))
assert len(NEW_DENIS_LEADS) == 30
slugs = [x["slug"] for x in NEW_DENIS_LEADS]
assert len(set(slugs)) == 30, "Duplicate slug in new list!"
print("All 30 unique and verified!")
