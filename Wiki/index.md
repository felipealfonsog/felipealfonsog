> "We must elevate ourselves above the dust of the world, and seek that Light which alone can guide us to the Temple of Truth."
>
> — *Albert Pike*

<div class="infobox">
    <table>
        <tr>
            <th colspan="2" class="infobox-header">Felipe Alfonso González</th>
        </tr>
        <tr>
            <td colspan="2" class="infobox-image">
                <img src="images/Perpicfagv2.jpg" alt="Profile Picture" style="width: 85px; height: 85px;">
            </td>
        </tr>
        <tr>
            <td colspan="2" class="infobox-caption">Profile Picture</td>
        </tr>
        <tr>
            <td class="infobox-label">Nacimiento</td>
            <td class="infobox-data">1979 (46 años)</td>
        </tr>
        <tr>
            <td class="infobox-label">Nacionalidad</td>
            <td class="infobox-data">Chilena</td>
        </tr>
        <tr>
            <td class="infobox-label">Etnicidad</td>
            <td class="infobox-data">Europea / Latinoamericana (orígenes familiares en Cataluña y Aragón, España – raíces judías sefardíes)</td>
        </tr>
        <tr>
            <td class="infobox-label">Idiomas</td>
            <td class="infobox-data">Español, Inglés, Francés, Afrikáans</td>
        </tr>
        <tr>
            <td class="infobox-label">Religión</td>
            <td class="infobox-data">Ateo secular, practicante del Budismo Zen como camino filosófico y meditativo. Afín a la Francmasonería por sus valores éticos y desarrollo personal. Descendencia judía sefardí.</td>
        </tr>
        <tr>
            <td class="infobox-label">Educación</td>
            <td class="infobox-data">
                Instituto Profesional AIEP<br>
                Universidad Mayor<br>
                Instituto Profesional IACC
            </td>
        </tr>
        <tr>
            <td class="infobox-label">Ocupación</td>
            <td class="infobox-data">Ingeniero en Informática</td>
        </tr>
        <tr>
            <td class="infobox-label">Cargo</td>
            <td class="infobox-data">Asesor, Investigador. Arquitecto de Sistemas y Analista en Ciberseguridad y Ciberinteligencia.</td>
        </tr>
        <tr>
            <td class="infobox-label">Ubicación</td>
            <td class="infobox-data">
                Santiago, Chile 🇨🇱<br>
                <small>Anteriormente: India, Sudáfrica, Nueva Zelanda, California (EE.UU.), Zúrich (Suiza)</small>
            </td>
        </tr>
        <tr>
            <td class="infobox-label">Email</td>
            <td class="infobox-data"><a href="mailto:felipe.gonzalez@gnlz.cl">felipe.gonzalez@gnlz.cl</a></td>
        </tr>
        <tr>
            <td class="infobox-label">Sitio Web</td>
            <td class="infobox-data"><a href="https://www.gnlz.cl" target="_blank">www.gnlz.cl</a></td>
        </tr>
        <tr>
            <td class="infobox-label">LinkedIn</td>
            <td class="infobox-data"><a href="https://www.linkedin.com/in/felipealfonsog" target="_blank">felipealfonsog</a></td>
        </tr>
        <tr>
            <td class="infobox-label">GitHub</td>
            <td class="infobox-data"><a href="https://github.com/felipealfonsog" target="_blank">felipealfonsog</a></td>
        </tr>
        <tr>
            <td class="infobox-label">Twitter (X)</td>
            <td class="infobox-data"><a href="https://twitter.com/felipealfonsog" target="_blank">felipealfonsog</a></td>
        </tr>
        <tr>
            <td colspan="2" class="userboxes">
                <img src="https://via.placeholder.com/200x25/f0f0f0/000000?text=Wikipedista+desde+26-09-2014" alt="Wikipedian since 2014">
                <img src="https://via.placeholder.com/200x25/1793D1/FFFFFF?text=Arch+Linux+User" alt="Arch Linux User">
                <img src="https://via.placeholder.com/200x25/AB2B28/FFFFFF?text=FreeBSD+User" alt="FreeBSD User">
            </td>
        </tr>
    </table>
</div>

**Felipe Alfonso González** es un Ingeniero en [Informática](computer_science.md) de [Chile](chile.md), especializado en [Arquitectura de Sistemas](systems_architecture.md) y [Ciberseguridad](cybersecurity.md), con una sólida formación en [ciberinteligencia](cyberintelligence.md) e [ingeniería de software](software_engineering.md). Su enfoque profesional se centra en la investigación y el desarrollo en áreas como [ingeniería de datos](data_engineering.md), [aprendizaje automático](machine_learning.md), [ciberseguridad](cybersecurity.md) y teoría de la [informática](computer_science.md).

## Perfil Académico

<figure class="img-float-right" style="width: 190px;">
  <img src="images/Informatik_thumb.png" alt="Visual summary of computing fields">
  <figcaption>Un resumen visual de los campos de la computación. El símbolo lambda (λ) representa comúnmente la teoría de lenguajes de programación.</figcaption>
</figure>

Felipe Alfonso González ha cursado estudios formales en informática, ciberseguridad e inteligencia de negocios en diversas instituciones de **Chile**, **España** y **Estados Unidos**.

Estudió en la **Universidad Mayor** (2007–2011), ubicada en Providencia, Santiago, donde fue miembro activo del Grupo de Usuarios de Linux de la universidad.

... y así sucesivamente con el resto del contenido.

<div class="clear"></div> ```

### Paso 4: Automatizar con GitHub Actions

Este archivo le dice a GitHub que construya y despliegue tu sitio cada vez que actualices la rama `main`.

Crea el archivo `.github/workflows/deploy-wiki.yml`:

```yaml
# .github/workflows/deploy-wiki.yml
name: Deploy Wiki to GitHub Pages

on:
  push:
    branches:
      - main  # o 'master', dependiendo de tu rama principal

jobs:
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.x

      - name: Install dependencies
        run: |
          pip install mkdocs
          pip install mkdocs-material

      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
