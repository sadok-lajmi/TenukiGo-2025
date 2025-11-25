# Patch et Installation de *sente* pour Python \> 3.10

Ce guide explique comment installer la librairie **sente** sous Windows
avec Python 3.11+ en appliquant quelques correctifs nécessaires (patchs
C++ et ajustements Python).

## Prérequis : Outils de Compilation C++

Pour compiler les modules natifs, vous devez disposer du compilateur C++
de Visual Studio.

### Installation des Visual Studio Build Tools

1.  Téléchargez l'installateur des **Visual Studio Build Tools**.
2.  Lancez l'installateur.
3.  Cochez l'option : **Desktop development with C++**.
4.  Laissez l'installation se terminer.

## Étape 1 : Préparer l'Environnement & Cloner le Dépôt

``` bash
mkdir sente_install
cd sente_install
git clone https://github.com/atw1020/sente.git sente-src
cd sente-src
```

## Étape 2 : Appliquer les Patches

### A. Modifier setup.py

Modifier la ligne (à priori ligne 79) :

``` python
python_requires=">=3.8.*"
```

en :

``` python
python_requires=">=3.8"
```

### B. Ajouter #include `<algorithm>`

Ajouter dans les fichiers suivants :

-   `src/Utils/Tree.h`
-   `src/Utils/SGF/SGFNode.cpp`


``` c++
#include <algorithm>
```

## Étape 3 : Installation Standard

``` bash
pip install .
cd ..
rmdir /s sente_install
```

## Étape 3 (bis) : Installation Alternative avec Meson + Ninja
Il est probable que l'étape 3 n'aie pas fonctionnée, voici un autre moyen de finaliser l'installation manuelle.

Installer les outils :

``` bash
pip install meson ninja
```

Puis, dans *x64 Native Tools Command Prompt for VS* :

``` bash
meson setup builddir --prefix=/ --buildtype=release
ninja -C builddir
```

Copier le fichier généré :

    sente.cp312-win_amd64.pyd

vers :

    .venv/Lib/site-packages

## Fin

Le module **sente** est maintenant compatible et utilisable avec Python 3.11+ !
