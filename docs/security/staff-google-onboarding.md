# Staff Google onboarding and sign-in diagnostics

This guide describes the source candidate in ADR-0018. Use it with the pilot only after a separately approved schema/image/service rollout and explicit recovery-permission provisioning. It does not authorize a live account action by itself.

## English

An authorized account manager creates a suspended staff account with the person's intended Google sign-in email and appropriate access profile. There is no manual Google identifier field. The person signs in with that Google account; Golden Rose records the verified identity while the account remains unavailable until activation. The manager reloads **Sign-in diagnostics**, confirms MFA enrollment deliberately, and activates the verified account with a reason. The person reloads **My staff account** and verifies workspace access.

Use **Manage access** for name, role and permission changes. These changes preserve the Google identity, sign-in email and MFA evidence.

| Diagnostic state | Next step |
| --- | --- |
| Waiting for Google sign-in | Ask the person to choose the assigned Google account, then reload diagnostics. An unavailable-account result before activation can be expected. |
| Legacy identity needs verification | Ask the person to sign in. Existing exact-subject access continues for active legitimate accounts. A verified sign-in records provenance; merely editing the account does not. |
| Google identity verified; account suspended | Confirm MFA enrollment and activate only after the intended person has completed onboarding. |
| Active with verified identity | Account evidence permits sign-in. If the browser still reports an error, clear the Golden Rose session, choose the intended Google account and retry. Record the safe error text and timing if it persists. |
| Deprovisioned | This account cannot be reactivated or restarted. Preserve its history and use a separately reviewed onboarding decision. |

For an invalid legacy binding or an incorrect assigned sign-in email, an administrator with the separate recovery permission can use **Restart Google sign-in** from diagnostics. This supports the same email. It suspends access and clears the binding/MFA evidence, while preserving the staff ID, history and permissions. The intended person signs in again; the manager then reconfirms MFA and activates the verified account. Account deletion/recreation is not the ordinary recovery workflow.

If a restart has an unknown result, keep the form open and use **Retry original restart**. Its email, reason and command remain fixed until the receipt resolves. A later permission or network error does not prove the original action failed. Do not begin another restart to work around uncertainty. A successful response is followed by a fresh account reload so later activity is visible.

Diagnostics are application evidence. They do not inspect Google factor configuration, force Google reauthentication or revoke provider sessions. Do not collect or share passwords, codes, tokens or raw Google subjects. A browser receiving a Google credential does not prove an authorized Golden Rose session.

## Español

Una persona autorizada crea una cuenta suspendida con el correo de Google previsto y el perfil de acceso correspondiente. No se ingresa un identificador manual de Google. La persona inicia sesión con esa cuenta de Google; Golden Rose verifica la identidad, pero mantiene la cuenta sin acceso hasta la activación. El administrador recarga **Diagnóstico de acceso**, confirma expresamente la inscripción de MFA y activa la cuenta con un motivo. La persona recarga **Mi cuenta del personal** y comprueba que puede acceder al espacio de trabajo.

Use **Administrar acceso** para cambiar el nombre, el rol o los permisos. Estos cambios conservan la identidad de Google, el correo de acceso y la evidencia de MFA.

| Estado del diagnóstico | Próximo paso |
| --- | --- |
| Esperando inicio de Google | Pida elegir la cuenta de Google asignada y recargue el diagnóstico. Antes de la activación, puede aparecer que la cuenta no está disponible. |
| Identidad anterior sin verificar | Pida iniciar sesión. Las cuentas activas legítimas conservan el acceso con su identidad existente; el inicio verificado registra la evidencia. Editar la cuenta no verifica la identidad. |
| Identidad de Google verificada; cuenta suspendida | Confirme la inscripción de MFA y active la cuenta después de completar la incorporación de la persona prevista. |
| Activa con identidad verificada | La evidencia permite iniciar sesión. Si continúa el error, borre la sesión de Golden Rose, elija la cuenta de Google prevista y vuelva a intentar. Registre el texto seguro del error y la hora si persiste. |
| Cuenta retirada | No se puede reactivar ni reiniciar. Conserve el historial y revise por separado cualquier nueva incorporación. |

Si la vinculación anterior es incorrecta o se asignó un correo equivocado, un administrador con permiso de recuperación puede usar **Reiniciar inicio de Google** desde el diagnóstico. Se permite conservar el mismo correo. El reinicio suspende el acceso y borra la evidencia de vinculación y MFA; conserva el identificador interno, el historial y los permisos. La persona inicia sesión otra vez; después, el administrador vuelve a confirmar MFA y activa la cuenta verificada.

Si el resultado del reinicio es incierto, mantenga abierto el formulario y use **Reintentar reinicio original**. No cambie el correo, el motivo ni la solicitud hasta resolver el resultado. Un error posterior de permisos o conexión no demuestra que la primera solicitud haya fallado.

El diagnóstico muestra evidencia de Golden Rose. No restablece factores de Google, no obliga a volver a autenticarse en Google y no revoca sus sesiones. No recopile ni comparta contraseñas, códigos, tokens ni identificadores internos de Google. Recibir una credencial de Google en el navegador no confirma el acceso autorizado a Golden Rose.
