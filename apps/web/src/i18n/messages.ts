export type MessageCatalog = {
  catalogVersion: 'Proposed';
  reviewStatus: 'Proposed';
  shellHeading: string;
  primaryNavigation: string;
  employersNav: string;
  switchLanguage: string;
  employersWorkspaceLabel: string;
  employerSearchHeading: string;
  employerSearchInstructions: string;
  employerSearchFormLabel: string;
  employerSearchNameLabel: string;
  employerSearchTypeLabel: string;
  employerSearchTypeAnyOption: string;
  employerTypeBusiness: string;
  employerTypeHousehold: string;
  employerSearchSubmit: string;
  employerSearchBusy: string;
  employerSearchSubmittedLabel: string;
  employerSearchNameError: string;
  employerSearchEmptyHeading: string;
  employerSearchEmptyBody: string;
  employerSearchResultsHeading: string;
  employerLifecycleDraft: string;
  employerSearchValidationFailureHeading: string;
  employerSearchValidationFailureBody: string;
  employerSearchForbiddenFailureHeading: string;
  employerSearchForbiddenFailureBody: string;
  employerSearchConflictFailureHeading: string;
  employerSearchConflictFailureBody: string;
  employerSearchUnavailableFailureHeading: string;
  employerSearchUnavailableFailureBody: string;
  employerSearchUnexpectedFailureHeading: string;
  employerSearchUnexpectedFailureBody: string;
  employerSearchRetry: string;
  employerSearchLoadMore: string;
  employerSearchPageValidationFailureHeading: string;
  employerSearchPageValidationFailureBody: string;
  employerSearchPageForbiddenFailureHeading: string;
  employerSearchPageForbiddenFailureBody: string;
  employerSearchPageConflictFailureHeading: string;
  employerSearchPageConflictFailureBody: string;
  employerSearchPageUnavailableFailureHeading: string;
  employerSearchPageUnavailableBody: string;
  employerSearchPageUnexpectedFailureHeading: string;
  employerSearchPageUnexpectedFailureBody: string;
  employerSearchRetryLoadMore: string;
  employerDetailLoadingHeading: string;
  employerDetailLoadingBody: string;
  employerDetailNameLabel: string;
  employerDetailTypeLabel: string;
  employerDetailLifecycleLabel: string;
  employerDetailSourceLabel: string;
  employerSourceStaffEntry: string;
  employerDetailNotFoundHeading: string;
  employerDetailNotFoundBody: string;
  employerDetailValidationHeading: string;
  employerDetailValidationBody: string;
  employerDetailForbiddenHeading: string;
  employerDetailForbiddenBody: string;
  employerDetailConflictHeading: string;
  employerDetailConflictBody: string;
  employerDetailUnavailableHeading: string;
  employerDetailUnavailableBody: string;
  employerDetailUnexpectedHeading: string;
  employerDetailUnexpectedBody: string;
  employerCreateHeading: string;
  employerCreateWarning: string;
  employerCreateTypeLabel: string;
  employerCreateNameLabel: string;
  employerCreateSubmit: string;
  employerCreateNameError: string;
  employerCreateTypeError: string;
  employerCreateValidationFailureHeading: string;
  employerCreateValidationFailureBody: string;
  employerCreateForbiddenFailureHeading: string;
  employerCreateForbiddenFailureBody: string;
  employerCreateSuccessHeading: string;
  employerCreateUnknownHeading: string;
  employerCreateUnknownBody: string;
  employerCreateUnknownRetry: string;
  employerCreateAbandonBody: string;
  employerCreateAbandonAction: string;
  employerCreateAbandonSearchFailure: string;
  employerCreateConflictHeading: string;
  employerCreateConflictAction: string;
  notFoundHeading: string;
  notFoundBody: string;
};

export const englishMessages: MessageCatalog = {
  catalogVersion: 'Proposed',
  reviewStatus: 'Proposed',
  shellHeading: 'Golden Rose Staff Workspace',
  primaryNavigation: 'Primary',
  employersNav: 'Employers',
  switchLanguage: 'Cambiar a español',
  employersWorkspaceLabel: 'Employers workspace',
  employerSearchHeading: 'Search for an employer',
  employerSearchInstructions: 'Use a bounded employer name fragment to begin a staff-only synthetic search.',
  employerSearchFormLabel: 'Employer search',
  employerSearchNameLabel: 'Employer name',
  employerSearchTypeLabel: 'Employer type',
  employerSearchTypeAnyOption: 'Any employer type',
  employerTypeBusiness: 'Business',
  employerTypeHousehold: 'Household',
  employerSearchSubmit: 'Search employers',
  employerSearchBusy: 'Searching employers.',
  employerSearchSubmittedLabel: 'Submitted search',
  employerSearchNameError: 'Enter 2 to 100 visible characters from the employer name.',
  employerSearchEmptyHeading: 'No matching employers',
  employerSearchEmptyBody: 'Try a different employer name fragment or clear the employer type filter.',
  employerSearchResultsHeading: 'Search results',
  employerLifecycleDraft: 'Draft',
  employerSearchValidationFailureHeading: 'Search could not run',
  employerSearchValidationFailureBody: 'Review the employer name fragment or employer type and try again.',
  employerSearchForbiddenFailureHeading: 'Search is not available for this staff session',
  employerSearchForbiddenFailureBody: 'This staff session is not allowed to run employer searches.',
  employerSearchConflictFailureHeading: 'Search requires a fresh staff action',
  employerSearchConflictFailureBody: 'Run the employer search again before continuing from this workspace state.',
  employerSearchUnavailableFailureHeading: 'Search is temporarily unavailable',
  employerSearchUnavailableFailureBody: 'Retry the same employer search when the service becomes available.',
  employerSearchUnexpectedFailureHeading: 'Search response could not be used',
  employerSearchUnexpectedFailureBody: 'Retry the search or change the filters before trying again.',
  employerSearchRetry: 'Retry search',
  employerSearchLoadMore: 'Load more employers',
  employerSearchPageValidationFailureHeading: 'More employers could not load',
  employerSearchPageValidationFailureBody: 'Run the employer search again before loading more employers.',
  employerSearchPageForbiddenFailureHeading: 'More employers are not available for this staff session',
  employerSearchPageForbiddenFailureBody: 'This staff session is not allowed to load more employers for the current search.',
  employerSearchPageConflictFailureHeading: 'More employers require a fresh search',
  employerSearchPageConflictFailureBody: 'Run the employer search again before loading more employers.',
  employerSearchPageUnavailableFailureHeading: 'More employers are temporarily unavailable',
  employerSearchPageUnavailableBody: 'Retry loading more employers when the service becomes available.',
  employerSearchPageUnexpectedFailureHeading: 'More employers response could not be used',
  employerSearchPageUnexpectedFailureBody: 'Run the employer search again before loading more employers.',
  employerSearchRetryLoadMore: 'Retry loading more employers',
  employerDetailLoadingHeading: 'Employer detail',
  employerDetailLoadingBody: 'Loading employer detail.',
  employerDetailNameLabel: 'Name',
  employerDetailTypeLabel: 'Type',
  employerDetailLifecycleLabel: 'Lifecycle',
  employerDetailSourceLabel: 'Source',
  employerSourceStaffEntry: 'Staff entry',
  employerDetailNotFoundHeading: 'Employer detail is no longer available',
  employerDetailNotFoundBody: 'The selected employer detail could not be found for this staff workspace.',
  employerDetailValidationHeading: 'Employer detail could not be displayed',
  employerDetailValidationBody: 'Select the employer again from the current search results.',
  employerDetailForbiddenHeading: 'Employer detail is not available for this staff session',
  employerDetailForbiddenBody: 'This staff session is not allowed to view the selected employer detail.',
  employerDetailConflictHeading: 'Employer detail requires a fresh search',
  employerDetailConflictBody: 'Run the employer search again before reopening employer detail.',
  employerDetailUnavailableHeading: 'Employer detail is temporarily unavailable',
  employerDetailUnavailableBody: 'Retry selecting the employer detail when the service becomes available.',
  employerDetailUnexpectedHeading: 'Employer detail response could not be used',
  employerDetailUnexpectedBody: 'Select the employer again or run the search again before reopening employer detail.',
  employerCreateHeading: 'Create a draft employer',
  employerCreateWarning: 'Create only fictional synthetic draft employers in this local staff workspace.',
  employerCreateTypeLabel: 'Create employer type',
  employerCreateNameLabel: 'Create employer name',
  employerCreateSubmit: 'Create draft employer',
  employerCreateNameError: 'Enter 1 to 200 visible characters for the employer name.',
  employerCreateTypeError: 'Select either Business or Household before creating a draft employer.',
  employerCreateValidationFailureHeading: 'Create draft employer could not be completed',
  employerCreateValidationFailureBody: 'Review the employer type or employer name and correct the draft employer before trying again.',
  employerCreateForbiddenFailureHeading: 'Create draft employer is not available for this staff session',
  employerCreateForbiddenFailureBody: 'This staff session is not allowed to create draft employers.',
  employerCreateSuccessHeading: 'Draft employer created',
  employerCreateUnknownHeading: 'Create outcome is unknown',
  employerCreateUnknownBody: 'Retry the same create attempt because it may already have succeeded.',
  employerCreateUnknownRetry: 'Retry same create attempt',
  employerCreateAbandonBody: 'The prior create may already have succeeded. Search for it before starting a changed create attempt.',
  employerCreateAbandonAction: 'Abandon unknown create and search',
  employerCreateAbandonSearchFailure: 'The required follow-up search could not complete. Retry the search before starting a changed create attempt.',
  employerCreateConflictHeading: 'Create is blocked until you search first',
  employerCreateConflictAction: 'Abandon blocked create and search',
  notFoundHeading: 'Page not found / Página no encontrada',
  notFoundBody: 'This placeholder route does not expose employer workflow data.',
};

export type Messages = MessageCatalog;

export const spanishMessages: MessageCatalog = {
  catalogVersion: 'Proposed',
  reviewStatus: 'Proposed',
  shellHeading: 'Espacio de trabajo del personal de Golden Rose',
  primaryNavigation: 'Principal',
  employersNav: 'Empleadores',
  switchLanguage: 'Switch to English',
  employersWorkspaceLabel: 'Espacio de trabajo de empleadores',
  employerSearchHeading: 'Buscar un empleador',
  employerSearchInstructions: 'Use un fragmento limitado del nombre del empleador para iniciar una búsqueda sintética solo para el personal.',
  employerSearchFormLabel: 'Búsqueda de empleadores',
  employerSearchNameLabel: 'Nombre del empleador',
  employerSearchTypeLabel: 'Tipo de empleador',
  employerSearchTypeAnyOption: 'Cualquier tipo de empleador',
  employerTypeBusiness: 'Empresa',
  employerTypeHousehold: 'Hogar',
  employerSearchSubmit: 'Buscar empleadores',
  employerSearchBusy: 'Buscando empleadores.',
  employerSearchSubmittedLabel: 'Búsqueda enviada',
  employerSearchNameError: 'Ingrese de 2 a 100 caracteres visibles del nombre del empleador.',
  employerSearchEmptyHeading: 'No hay empleadores coincidentes',
  employerSearchEmptyBody: 'Pruebe un fragmento diferente del nombre del empleador o quite el filtro de tipo de empleador.',
  employerSearchResultsHeading: 'Resultados de la búsqueda',
  employerLifecycleDraft: 'Borrador',
  employerSearchValidationFailureHeading: 'La búsqueda no pudo ejecutarse',
  employerSearchValidationFailureBody: 'Revise el fragmento del nombre del empleador o el tipo de empleador e inténtelo de nuevo.',
  employerSearchForbiddenFailureHeading: 'La búsqueda no está disponible para esta sesión del personal',
  employerSearchForbiddenFailureBody: 'Esta sesión del personal no puede ejecutar búsquedas de empleadores.',
  employerSearchConflictFailureHeading: 'La búsqueda requiere una acción nueva del personal',
  employerSearchConflictFailureBody: 'Ejecute la búsqueda del empleador de nuevo antes de continuar desde este estado del espacio de trabajo.',
  employerSearchUnavailableFailureHeading: 'La búsqueda no está disponible temporalmente',
  employerSearchUnavailableFailureBody: 'Vuelva a intentar la misma búsqueda de empleadores cuando el servicio esté disponible.',
  employerSearchUnexpectedFailureHeading: 'La respuesta de la búsqueda no pudo usarse',
  employerSearchUnexpectedFailureBody: 'Vuelva a intentar la búsqueda o cambie los filtros antes de intentarlo de nuevo.',
  employerSearchRetry: 'Reintentar búsqueda',
  employerSearchLoadMore: 'Cargar más empleadores',
  employerSearchPageValidationFailureHeading: 'No se pudieron cargar más empleadores',
  employerSearchPageValidationFailureBody: 'Ejecute la búsqueda del empleador de nuevo antes de cargar más empleadores.',
  employerSearchPageForbiddenFailureHeading: 'Más empleadores no están disponibles para esta sesión del personal',
  employerSearchPageForbiddenFailureBody: 'Esta sesión del personal no tiene permiso para cargar más empleadores para la búsqueda actual.',
  employerSearchPageConflictFailureHeading: 'Más empleadores requieren una búsqueda nueva',
  employerSearchPageConflictFailureBody: 'Ejecute la búsqueda del empleador de nuevo antes de cargar más empleadores.',
  employerSearchPageUnavailableFailureHeading: 'Más empleadores no están disponibles temporalmente',
  employerSearchPageUnavailableBody: 'Vuelva a intentar cargar más empleadores cuando el servicio esté disponible.',
  employerSearchPageUnexpectedFailureHeading: 'La respuesta de más empleadores no pudo usarse',
  employerSearchPageUnexpectedFailureBody: 'Ejecute la búsqueda del empleador de nuevo antes de cargar más empleadores.',
  employerSearchRetryLoadMore: 'Reintentar cargar más empleadores',
  employerDetailLoadingHeading: 'Detalle del empleador',
  employerDetailLoadingBody: 'Cargando el detalle del empleador.',
  employerDetailNameLabel: 'Nombre',
  employerDetailTypeLabel: 'Tipo',
  employerDetailLifecycleLabel: 'Estado',
  employerDetailSourceLabel: 'Origen',
  employerSourceStaffEntry: 'Registro del personal',
  employerDetailNotFoundHeading: 'El detalle del empleador ya no está disponible',
  employerDetailNotFoundBody: 'No se pudo encontrar el detalle del empleador seleccionado para este espacio de trabajo del personal.',
  employerDetailValidationHeading: 'No se pudo mostrar el detalle del empleador',
  employerDetailValidationBody: 'Seleccione el empleador de nuevo desde los resultados actuales de la búsqueda.',
  employerDetailForbiddenHeading: 'El detalle del empleador no está disponible para esta sesión del personal',
  employerDetailForbiddenBody: 'Esta sesión del personal no tiene permiso para ver el detalle del empleador seleccionado.',
  employerDetailConflictHeading: 'El detalle del empleador requiere una búsqueda nueva',
  employerDetailConflictBody: 'Ejecute la búsqueda del empleador de nuevo antes de volver a abrir el detalle del empleador.',
  employerDetailUnavailableHeading: 'El detalle del empleador no está disponible temporalmente',
  employerDetailUnavailableBody: 'Vuelva a seleccionar el detalle del empleador cuando el servicio esté disponible.',
  employerDetailUnexpectedHeading: 'La respuesta del detalle del empleador no pudo usarse',
  employerDetailUnexpectedBody: 'Seleccione el empleador de nuevo o ejecute la búsqueda otra vez antes de volver a abrir el detalle del empleador.',
  employerCreateHeading: 'Crear un empleador en borrador',
  employerCreateWarning: 'Cree solo empleadores en borrador ficticios y sintéticos en este espacio de trabajo local del personal.',
  employerCreateTypeLabel: 'Tipo de empleador para crear',
  employerCreateNameLabel: 'Nombre del empleador para crear',
  employerCreateSubmit: 'Crear empleador en borrador',
  employerCreateNameError: 'Ingrese entre 1 y 200 caracteres visibles para el nombre del empleador.',
  employerCreateTypeError: 'Seleccione Business o Household antes de crear un empleador en borrador.',
  employerCreateValidationFailureHeading: 'No se pudo completar la creación del empleador en borrador',
  employerCreateValidationFailureBody: 'Revise el tipo o el nombre del empleador y corrija el empleador en borrador antes de intentarlo de nuevo.',
  employerCreateForbiddenFailureHeading: 'La creación del empleador en borrador no está disponible para esta sesión del personal',
  employerCreateForbiddenFailureBody: 'Esta sesión del personal no tiene permiso para crear empleadores en borrador.',
  employerCreateSuccessHeading: 'Empleador en borrador creado',
  employerCreateUnknownHeading: 'El resultado de la creación es desconocido',
  employerCreateUnknownBody: 'Vuelva a intentar la misma creación porque puede que ya se haya realizado con éxito.',
  employerCreateUnknownRetry: 'Reintentar la misma creación',
  employerCreateAbandonBody: 'La creación anterior puede que ya se haya realizado con éxito. Búsquela antes de iniciar un intento de creación cambiado.',
  employerCreateAbandonAction: 'Abandonar la creación desconocida y buscar',
  employerCreateAbandonSearchFailure: 'La búsqueda de seguimiento requerida no pudo completarse. Reintente la búsqueda antes de iniciar un intento de creación cambiado.',
  employerCreateConflictHeading: 'La creación está bloqueada hasta que busque primero',
  employerCreateConflictAction: 'Abandonar la creación bloqueada y buscar',
  notFoundHeading: 'Page not found / Página no encontrada',
  notFoundBody: 'Esta ruta provisional no expone datos del flujo de trabajo de empleadores.',
};
