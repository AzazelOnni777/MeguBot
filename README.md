![MeguBot](https://telegra.ph/file/4645f09a45e70298624d7.jpg)
# Megu Bot 
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://perso.crans.org/besson/LICENSE.html) [![Open Source Love svg2](https://badges.frapsoft.com/os/v2/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)


Un bot modular de Telegram Python en español que se ejecuta en python3 con una base de datos sqlalchemy.

Originalmente un fork de SaitamaRobot.

Se puede encontrar en telegram como [MeguBot](https://t.me/MeguABR_Bot).

Puede comunicarse con el grupo de soporte en [Megu Support](https://t.me/MeguSupport), donde puede solicitar ayuda sobre @MeguABR_Bot, descubrir/solicitar nuevas funciones, informar errores y mantenerse informado cuando sea hay una nueva actualización disponible.

## Cómo configurar/implementar.

### Lea estas notas detenidamente antes de continuar
 - Edite cualquier mención de @MeguSupport en su propio chat de soporte.
 - No admitimos bifurcaciones, una vez que bifurque el bot y despliegue el dolor de cabeza de los errores y el soporte sea suyo, no venga a nuestro chat de soporte pidiendo ayuda técnica.
 - Su código debe ser de código abierto y debe haber un enlace al repositorio de su bifurcación en la respuesta de inicio del bot. [Ver esto](https://github.com/NachABR/MeguBot/blob/f3c76b1c84e14b88a93f3f5a57b4ee748a83c551/MeguBot/__main__.py#L24)
 - Si viene a nuestro chat de soporte en Telegram pidiendo ayuda sobre una "bifurcación" o un problema técnico con un módulo, terminará siendo ignorado o prohibido.
 - Por último, si se encuentra que ejecuta este repositorio sin que el código sea de código abierto o el enlace del repositorio no se menciona en el bot, le enviaremos una gban en nuestra red debido a una violación de la licencia, puede hacerlo sea un idiota y no respete el código fuente abierto (no nos importa), pero no lo tendremos en nuestros chats.
<details>
<summary>Pasos para implementar en Heroku!!</summary>

```
Complete todos los detalles, ¡Implemente!
Ahora vaya a https://dashboard.heroku.com/apps/(app-name)/resources (Reemplace (app-name) con el nombre de su aplicación)
Encienda el dinamómetro del trabajador (no se preocupe, es gratis :D) y Webhook
Ahora envíe el bot /start. Si no responde, vaya a https://dashboard.heroku.com/apps/(app-name)/settings y elimine el webhook y el puerto.
```
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/NachABR/MeguBot.git)

</details>
<details>
 <summary>Pasos para hostearlo!!</summary>


Nota: Este conjunto de instrucciones es solo una copia y pegado de Marie, tenga en cuenta que [Megu Support](https://t.me/MeguSupport) tiene como objetivo manejar el soporte para @MeguABR_Bot y no cómo configurar su propia bifurcación. Si encuentra esto un poco confuso/difícil de entender, le recomendamos que pregunte a un desarrollador, por favor evite preguntar cómo configurar la instancia del bot en el chat de soporte, tiene como objetivo ayudar a nuestra propia instancia del bot y no a las bifurcaciones.

  ## Configuración del bot (¡lea esto antes de intentar usarlo!):
¡Asegúrese de usar python3.6, ya que no puedo garantizar que todo funcione como se esperaba en versiones anteriores de Python!
Esto se debe a que el análisis de rebajas se realiza iterando a través de un dictado, que está ordenado por defecto en 3.6.

  ### Configuración

Hay dos formas posibles de configurar su bot: un archivo config.py o variables ENV.

La versión preferida es usar un archivo `config.py`, ya que facilita ver todas las configuraciones agrupadas.
Este archivo debe colocarse en su carpeta `MeguBot`, junto con el archivo` __main __. Py`.
Aquí es donde se cargará su token de bot, así como el URI de su base de datos (si está usando una base de datos), y la mayoría de
sus otras configuraciones.

Se recomienda importar sample_config y extender la clase Config, ya que esto asegurará que su configuración contenga todos
valores predeterminados establecidos en sample_config, lo que facilita la actualización.

Un ejemplo de archivo `config.py` podría ser:
```
from MeguBot.sample_config import Config

class Development(Config):
    OWNER_ID = 254318997 # Su ID de telegram.
    OWNER_USERNAME = "SonOfLars" # Su nombre de usuario de telegram.
    API_KEY = "your bot api key" # Su clave api, tal como la proporciona @botfather.
    SQLALCHEMY_DATABASE_URI = 'postgresql://nombredeusuario:contraseña@localhost:5432/database' # Credenciales de base de datos de muestra.
    MESSAGE_DUMP = '-1234567890' # Algún chat grupal donde su bot este ahí.
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [18673980, 83489514] # Lista de identificadores de usuarios que tienen acceso superusuario al bot.
    LOAD = []
    NO_LOAD = ['translation']
```

Si no puede tener un archivo config.py (EG en Heroku), también es posible usar variables de entorno.
Se admiten las siguientes variables de entorno:
 - `ENV`: Establecer esto en ANYTHING habilitará las variables env

 - `TOKEN`: Su token de bot, como una cadena.
 - `OWNER_ID`: un número entero que consiste en su ID de propietario
 - `OWNER_USERNAME`: Su nombre de usuario

 - `DATABASE_URL`: URL de su base de datos
 - `MESSAGE_DUMP`: Opcional: Un chat donde se almacenan sus mensajes guardados respondidos, para evitar que las personas eliminen sus mensajes.
 - `LOAD`: Lista de módulos separados por espacios que le gustaría cargar.
 - `NO_LOAD`: Lista de módulos separados por espacios que no le gustaría cargar.
 - `WEBHOOK`: Configurar esto en ANYTHING habilitará webhooks cuando esté en modo ENV.
 mensajes
 - `URL`: La URL a la que debe conectarse su webhook (solo se necesita para el modo webhook).

 - `SUDO_USERS`: Una lista separada por espacios de user_ids que deben considerarse superusuario.
