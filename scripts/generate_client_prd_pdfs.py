from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path('/Users/genie/Desktop/golden_rose_project/docs/client-deliverables')
OUT.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    'ClientTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18,
    leading=22, alignment=TA_CENTER, textColor=colors.HexColor('#6B1D2A'), spaceAfter=5,
)
SUBTITLE = ParagraphStyle(
    'ClientSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=10,
    leading=13, alignment=TA_CENTER, textColor=colors.HexColor('#555555'), spaceAfter=14,
)
H1 = ParagraphStyle(
    'ClientH1', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=13,
    leading=16, textColor=colors.HexColor('#6B1D2A'), spaceBefore=10, spaceAfter=5,
)
H2 = ParagraphStyle(
    'ClientH2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10.5,
    leading=13, textColor=colors.HexColor('#333333'), spaceBefore=7, spaceAfter=3,
)
BODY = ParagraphStyle(
    'ClientBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=9.2,
    leading=12.3, spaceAfter=5,
)
BULLET = ParagraphStyle(
    'ClientBullet', parent=BODY, leftIndent=13, firstLineIndent=-8, bulletIndent=3, spaceAfter=2,
)
SMALL = ParagraphStyle(
    'ClientSmall', parent=BODY, fontSize=8, leading=10, textColor=colors.HexColor('#555555'),
)


def p(text, style=BODY):
    return Paragraph(escape(text).replace('\n', '<br/>'), style)


def bullet(text):
    return Paragraph(escape(text), BULLET, bulletText='-')


def section(title, blocks):
    content = [p(title, H1)]
    for block in blocks:
        if isinstance(block, tuple) and block[0] == 'h2':
            content.append(p(block[1], H2))
        elif isinstance(block, tuple) and block[0] == 'bullets':
            content.extend(bullet(item) for item in block[1])
        else:
            content.append(p(block))
    return content


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D8D8D8'))
    canvas.line(doc.leftMargin, 0.53 * inch, letter[0] - doc.rightMargin, 0.53 * inch)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#666666'))
    canvas.drawString(doc.leftMargin, 0.35 * inch, 'Golden Rose Employment Agency | Client discussion draft')
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.35 * inch, f'Page {doc.page}')
    canvas.restoreState()


def rollout_table(rows):
    data = [[p(a, SMALL), p(b, SMALL), p(c, SMALL)] for a, b, c in rows]
    data.insert(0, [p('Stage', SMALL), p('Focus', SMALL), p('Value / gate', SMALL)])
    table = Table(data, colWidths=[0.72 * inch, 2.34 * inch, 3.58 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6B1D2A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#D0D0D0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FAF7F7')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def build_english():
    story = [
        p('Golden Rose Employment Agency', TITLE),
        p('Client discussion PRD - draft v0.2', SUBTITLE),
        p('Purpose: A short discussion draft for the seven-week engagement. It describes the direction recommended from discovery so far. It does not approve legal wording, fee rules, vendors, or production-data use.', SMALL),
    ]
    story += section('The problem we are solving', [
        'Golden Rose currently manages a fast-moving staffing operation through paper records, spreadsheets, Trello, Google Calendar, phone calls, WhatsApp, and email. The information is useful, but it is spread across people and systems.',
        ('bullets', [
            'Staff re-enter or search for the same information in several places.',
            'It is difficult to see the full history of an employer request, worker referral, assignment, receipt, or follow-up.',
            'Requests that arrive outside normal hours are harder to coordinate and track.',
            'Sensitive worker, employer, document, payment, and location information needs clearer access controls.',
            'Current records do not make corrections, cancellations, refunds, or changes easy to trace.',
        ]),
        'The office also needs browser-based tools that run reliably on existing computers.',
    ])
    story += section('Our recommendation', [
        'Build a bilingual, compliance-first Golden Rose operations platform. It should give staff one reliable place to manage agency work, while giving workers and employers clear, limited self-service paths.',
        ('bullets', [
            'Track employer requests, workers, schedules, assignments, referrals, and follow-up.',
            'Search records by employer, contact, worksite, role, date, status, worker, and referral history.',
            'Send workers an approved job description before referral.',
            'Track documents, receipts, payments, corrections, and delivery history.',
            'Record who changed what, when, and why.',
        ]),
        'The system should support staff judgment. It should not make automatic hiring, ranking, screening, or placement decisions.',
    ])
    story += section('Who it is for', [
        ('h2', 'Agency staff'),
        'A secure workspace for managing requests, assignments, referrals, documents, receipts, corrections, and follow-up from one shared view.',
        ('h2', 'Employers'),
        'A controlled way to submit a staffing request, receive agency-approved updates, and receive only the information needed for the relationship.',
        ('h2', 'Workers / job seekers'),
        'A Spanish-first, English-equivalent experience for a basic profile, availability, work interests, communication preferences, job details, and worker-appropriate documents.',
    ])
    story += section('What we propose to build', [
        ('h2', 'A staff work queue and searchable operational record'),
        'The current workbook combines employer, contact, worksite, role, schedule, assignment, and follow-up information in one row. The new platform should keep these as related records: employer, contact, worksite, staffing request, shift need, worker, assignment, referral/delivery event, placement, and audit history. Month and calendar views should come from real dates, not separate monthly files.',
        ('h2', 'A controlled employer-request workflow'),
        'Employer request -> agency review -> approved worker-facing job description -> referral -> placement and follow-up. Exact household or worksite addresses should remain private until there is an approved operational reason to share them.',
        ('h2', 'Staged worker onboarding'),
        'Start with basic contact information, language preference, availability, work interests, approved skills/preferences, communication choices, and agency review. References, background information, identity verification, and other sensitive data require a separately approved purpose and process.',
        ('h2', 'Controlled documents and corrections'),
        'Keep job requests, job descriptions, disclosures, agreements, receipts, payments, and consent records distinct. Once an important record is issued, preserve the original. Corrections, voids, refunds, and replacements should create linked records rather than silently changing history.',
    ])
    story += section('English and Spanish experience', [
        'English/Spanish parity is required across the affected worker, employer, staff, document, notification, validation, and support workflows. Users should choose and be able to change their language preference. Existing bilingual forms are useful source material, but legal or consent wording must be approved before use.',
    ])
    story += section('Privacy, fairness, and security', [
        ('h2', 'Separate public and staff access'),
        'Worker and employer access must be separate from agency administration. Public users must not be able to reach staff records by changing a role, link, session, or request. Staff access should use stronger controls, including separate sessions, role-based access, MFA, and audit records for sensitive actions.',
        ('h2', 'Data and matching boundaries'),
        'The platform should not use protected traits, health/disability information, nationality, religion, criminal history, credit history, salary history, or similar proxy information as default filters or matching rules. Sensitive free-text requests need agency review and, where needed, approved replacement language. Referrals remain human-reviewed.',
    ])
    story += section('Rollout plan', [
        'Golden Rose has approved a staged delivery approach. We recommend small, testable releases instead of trying to launch every feature at once.',
    ])
    story.append(rollout_table([
        ('Week 1', 'Discovery, workflow validation, pilot selection', 'Agreement on the first build target'),
        ('Week 2', 'Security, data model, staff permissions, test environment', 'Safe foundation for a pilot'),
        ('Week 3', 'Limited staff pilot: request tracking and search', 'A shared work queue'),
        ('Week 4', 'Employer request workflow and agency review', 'Better intake and request visibility'),
        ('Week 5', 'Worker onboarding, language preference, job details', 'Clearer worker experience'),
        ('Week 6', 'Referral, placement, documents, receipts, corrections', 'Governed operational records'),
        ('Week 7', 'Acceptance, recovery checks, training, release decision', 'Readiness decision for wider use'),
    ]))
    story += section('Conditions before real data or production use', [
        ('bullets', [
            'Agree on what data is needed and who may access or change it.',
            'Confirm staff account and MFA procedures.',
            'Approve retention, deletion, export, incident, and support procedures.',
            'Verify encryption, audit logging, backups, and a tested restore process.',
            'Confirm English/Spanish and accessibility readiness.',
            'Define correction, rollback/recovery, and manual fallback procedures.',
            'Obtain client acceptance for the released workflow.',
        ]),
    ])
    story += section('Decisions needed from Golden Rose', [
        ('bullets', [
            'Which staff workflow should be the first pilot?',
            'Which current records are authoritative today?',
            'Which staff roles exist, and what should each role be allowed to see or change?',
            'Which legal documents and business policies are approved sources for fees, receipts, agreements, retention, and corrections?',
            'What information can be used in a pilot, and what must wait?',
            'Which integrations are genuinely needed first?',
            'Who will serve as client owner, pilot tester, support contact, and approval authority?',
        ]),
    ])
    story += section('Proposed client decision', [
        'Approve a staff-first, bilingual, compliance-first pilot that centralizes core operations, separates worker/employer access from staff administration, preserves attributable history, uses human review for referrals and placements, and requires approved legal and business sources before automating documents, fees, receipts, or retention rules.',
        'This decision does not approve production-data collection, legal automation, vendor selection, infrastructure changes, or public launch without the release gates above.',
    ])
    return story


def build_spanish():
    story = [
        p('Golden Rose Employment Agency', TITLE),
        p('PRD para conversacion con el cliente - borrador v0.2', SUBTITLE),
        p('Proposito: Este es un borrador breve para conversar durante el compromiso de siete semanas. Describe la direccion recomendada a partir del descubrimiento realizado hasta ahora. No aprueba lenguaje legal, reglas de tarifas, proveedores ni uso de datos de produccion.', SMALL),
    ]
    story += section('El problema que queremos resolver', [
        'Golden Rose actualmente maneja una operacion de contratacion de personal que cambia rapidamente mediante registros en papel, hojas de calculo, Trello, Google Calendar, llamadas telefonicas, WhatsApp y correo electronico. La informacion es util, pero esta distribuida entre personas y sistemas.',
        ('bullets', [
            'El personal vuelve a ingresar o busca la misma informacion en varios lugares.',
            'Es dificil ver el historial completo de una solicitud de empleador, referencia de trabajador, asignacion, recibo o seguimiento.',
            'Las solicitudes que llegan fuera del horario normal son mas dificiles de coordinar y rastrear.',
            'La informacion sensible de trabajadores, empleadores, documentos, pagos y ubicaciones necesita controles de acceso mas claros.',
            'Los registros actuales no facilitan el seguimiento de correcciones, cancelaciones, reembolsos o cambios.',
        ]),
        'La oficina tambien necesita herramientas basadas en el navegador que funcionen de manera confiable en las computadoras existentes.',
    ])
    story += section('Nuestra recomendacion', [
        'Crear una plataforma bilingue y centrada en el cumplimiento para las operaciones de Golden Rose. Debe dar al personal un lugar confiable para manejar el trabajo de la agencia y, al mismo tiempo, ofrecer a trabajadores y empleadores rutas claras y limitadas de autoservicio.',
        ('bullets', [
            'Rastrear solicitudes de empleadores, trabajadores, horarios, asignaciones, referencias y seguimiento.',
            'Buscar registros por empleador, contacto, lugar de trabajo, puesto, fecha, estado, trabajador e historial de referencias.',
            'Enviar al trabajador una descripcion de trabajo aprobada antes de una referencia.',
            'Rastrear documentos, recibos, pagos, correcciones e historial de entrega.',
            'Registrar quien cambio algo, cuando y por que.',
        ]),
        'El sistema debe apoyar el criterio del personal. No debe tomar decisiones automaticas de contratacion, clasificacion, seleccion o colocacion.',
    ])
    story += section('Para quien es', [
        ('h2', 'Personal de la agencia'),
        'Un espacio de trabajo seguro para manejar solicitudes, asignaciones, referencias, documentos, recibos, correcciones y seguimiento desde una vista compartida.',
        ('h2', 'Empleadores'),
        'Una forma controlada de enviar una solicitud de personal, recibir actualizaciones aprobadas por la agencia y recibir solo la informacion necesaria para la relacion.',
        ('h2', 'Trabajadores / personas que buscan empleo'),
        'Una experiencia primero en espanol y equivalente en ingles para crear un perfil basico, indicar disponibilidad e intereses laborales, elegir preferencias de comunicacion, revisar detalles del trabajo y recibir documentos apropiados.',
    ])
    story += section('Lo que proponemos crear', [
        ('h2', 'Una cola de trabajo y un registro operativo con busqueda'),
        'El libro de trabajo actual combina empleador, contacto, lugar de trabajo, puesto, horario, asignacion y seguimiento en una sola fila. La nueva plataforma debe mantener estos como registros relacionados: empleador, contacto, lugar de trabajo, solicitud de personal, necesidad de turno, trabajador, asignacion, evento de referencia/entrega, colocacion e historial de auditoria. Las vistas mensuales y de calendario deben salir de fechas reales, no de archivos mensuales separados.',
        ('h2', 'Un flujo controlado de solicitudes de empleadores'),
        'Solicitud del empleador -> revision de la agencia -> descripcion de trabajo aprobada para el trabajador -> referencia -> colocacion y seguimiento. Las direcciones exactas de hogares o lugares de trabajo deben mantenerse privadas hasta que exista una razon operativa aprobada para compartirlas.',
        ('h2', 'Incorporacion gradual de trabajadores'),
        'Comenzar con informacion basica de contacto, preferencia de idioma, disponibilidad, intereses laborales, habilidades/preferencias aprobadas, opciones de comunicacion y revision de la agencia. Las referencias, antecedentes, verificacion de identidad y otros datos sensibles necesitan un proposito y proceso aprobados por separado.',
        ('h2', 'Documentos y correcciones controlados'),
        'Mantener separadas las solicitudes de trabajo, descripciones de trabajo, divulgaciones, acuerdos, recibos, pagos y registros de consentimiento. Cuando se emita un registro importante, se debe conservar el original. Las correcciones, anulaciones, reembolsos y reemplazos deben crear registros vinculados en vez de cambiar el historial sin dejar rastro.',
    ])
    story += section('Experiencia en ingles y espanol', [
        'Se requiere paridad entre ingles y espanol en los flujos relevantes para trabajadores, empleadores, personal, documentos, notificaciones, validaciones y soporte. Las personas deben elegir y poder cambiar su preferencia de idioma. Los formularios bilingues existentes son material de referencia, pero el lenguaje legal o de consentimiento debe aprobarse antes de usarse.',
    ])
    story += section('Privacidad, equidad y seguridad', [
        ('h2', 'Acceso publico y acceso del personal separados'),
        'El acceso de trabajadores y empleadores debe estar separado de la administracion de la agencia. Los usuarios publicos no deben poder llegar a registros del personal al cambiar un rol, enlace, sesion o solicitud. El acceso del personal debe usar controles mas fuertes, incluyendo sesiones separadas, acceso por rol, MFA y registros de auditoria para acciones sensibles.',
        ('h2', 'Limites para los datos y la seleccion'),
        'La plataforma no debe usar caracteristicas protegidas, informacion de salud/discapacidad, nacionalidad, religion, historial penal, historial crediticio, historial salarial o informacion similar como filtros o reglas de seleccion predeterminadas. Las solicitudes de texto libre que sean sensibles requieren revision de la agencia y, cuando sea necesario, lenguaje de reemplazo aprobado. Las referencias deben seguir siendo revisadas por personas.',
    ])
    story += section('Plan de implementacion', [
        'Golden Rose ha aprobado un enfoque de entrega por etapas. Recomendamos lanzamientos pequenos y comprobables en vez de intentar lanzar todas las funciones a la vez.',
    ])
    rows = [
        ('Semana 1', 'Descubrimiento, validacion del flujo, seleccion del piloto', 'Acuerdo sobre el primer objetivo de construccion'),
        ('Semana 2', 'Seguridad, modelo de datos, permisos, entorno de prueba', 'Base segura para un piloto'),
        ('Semana 3', 'Piloto limitado: seguimiento y busqueda de solicitudes', 'Una cola de trabajo compartida'),
        ('Semana 4', 'Solicitud del empleador y revision de la agencia', 'Mejor recepcion y visibilidad de solicitudes'),
        ('Semana 5', 'Incorporacion de trabajadores, idioma y detalles del trabajo', 'Experiencia mas clara para el trabajador'),
        ('Semana 6', 'Referencia, colocacion, documentos, recibos y correcciones', 'Registros operativos controlados'),
        ('Semana 7', 'Aceptacion, recuperacion, capacitacion y decision de lanzamiento', 'Decision de preparacion para uso mas amplio'),
    ]
    # Localized header labels after table creation.
    table = rollout_table(rows)
    table._cellvalues[0] = [p('Etapa', SMALL), p('Enfoque', SMALL), p('Valor / control', SMALL)]
    story.append(table)
    story += section('Condiciones antes de usar datos reales o produccion', [
        ('bullets', [
            'Acordar que datos son necesarios y quien puede acceder a ellos o cambiarlos.',
            'Confirmar los procedimientos para cuentas del personal y MFA.',
            'Aprobar los procedimientos de retencion, eliminacion, exportacion, incidentes y soporte.',
            'Verificar cifrado, registros de auditoria, copias de seguridad y una restauracion probada.',
            'Confirmar la preparacion de ingles/espanol y accesibilidad.',
            'Definir procedimientos de correccion, recuperacion y alternativa manual.',
            'Obtener la aceptacion del cliente para el flujo liberado.',
        ]),
    ])
    story += section('Decisiones necesarias de Golden Rose', [
        ('bullets', [
            'Que flujo de trabajo del personal debe ser el primer piloto?',
            'Que registros actuales son la fuente autorizada hoy?',
            'Que roles del personal existen y que debe poder ver o cambiar cada rol?',
            'Que documentos legales y politicas comerciales son fuentes aprobadas para tarifas, recibos, acuerdos, retencion y correcciones?',
            'Que informacion puede usarse en un piloto y que debe esperar?',
            'Que integraciones se necesitan realmente primero?',
            'Quien sera el responsable del cliente, probador del piloto, contacto de soporte y autoridad de aprobacion?',
        ]),
    ])
    story += section('Decision propuesta para el cliente', [
        'Aprobar un piloto primero para el personal, bilingue y centrado en el cumplimiento. El piloto centralizaria las operaciones principales, separaria el acceso de trabajadores/empleadores de la administracion del personal, conservaria un historial atribuible, usaria revision humana para referencias y colocaciones, y exigiria fuentes legales y comerciales aprobadas antes de automatizar documentos, tarifas, recibos o reglas de retencion.',
        'Esta decision no aprueba la recopilacion de datos de produccion, automatizacion legal, seleccion de proveedores, cambios de infraestructura ni lanzamiento publico sin los controles de liberacion descritos arriba.',
    ])
    return story


def make_pdf(path, story):
    doc = SimpleDocTemplate(
        str(path), pagesize=letter, leftMargin=0.68 * inch, rightMargin=0.68 * inch,
        topMargin=0.58 * inch, bottomMargin=0.72 * inch, title='Golden Rose Employment Agency - Client Discussion PRD',
        author='Golden Rose Employment Agency engagement team',
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == '__main__':
    make_pdf(OUT / 'golden-rose-client-prd-en.pdf', build_english())
    make_pdf(OUT / 'golden-rose-client-prd-es.pdf', build_spanish())
    print(OUT / 'golden-rose-client-prd-en.pdf')
    print(OUT / 'golden-rose-client-prd-es.pdf')
