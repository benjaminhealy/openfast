#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "nwtclibs" for configuration "Release"
set_property(TARGET nwtclibs APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(nwtclibs PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libnwtclibs.a"
  )

list(APPEND _cmake_import_check_targets nwtclibs )
list(APPEND _cmake_import_check_files_for_nwtclibs "${_IMPORT_PREFIX}/lib/libnwtclibs.a" )

# Import target "versioninfolib" for configuration "Release"
set_property(TARGET versioninfolib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(versioninfolib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libversioninfolib.a"
  )

list(APPEND _cmake_import_check_targets versioninfolib )
list(APPEND _cmake_import_check_files_for_versioninfolib "${_IMPORT_PREFIX}/lib/libversioninfolib.a" )

# Import target "ifwlib" for configuration "Release"
set_property(TARGET ifwlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ifwlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libifwlib.a"
  )

list(APPEND _cmake_import_check_targets ifwlib )
list(APPEND _cmake_import_check_files_for_ifwlib "${_IMPORT_PREFIX}/lib/libifwlib.a" )

# Import target "inflowwind_driver" for configuration "Release"
set_property(TARGET inflowwind_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(inflowwind_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/inflowwind_driver"
  )

list(APPEND _cmake_import_check_targets inflowwind_driver )
list(APPEND _cmake_import_check_files_for_inflowwind_driver "${_IMPORT_PREFIX}/bin/inflowwind_driver" )

# Import target "ifw_c_binding" for configuration "Release"
set_property(TARGET ifw_c_binding APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ifw_c_binding PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libifw_c_binding.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libifw_c_binding.dylib"
  )

list(APPEND _cmake_import_check_targets ifw_c_binding )
list(APPEND _cmake_import_check_files_for_ifw_c_binding "${_IMPORT_PREFIX}/lib/libifw_c_binding.dylib" )

# Import target "extloadslib" for configuration "Release"
set_property(TARGET extloadslib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(extloadslib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libextloadslib.a"
  )

list(APPEND _cmake_import_check_targets extloadslib )
list(APPEND _cmake_import_check_files_for_extloadslib "${_IMPORT_PREFIX}/lib/libextloadslib.a" )

# Import target "aerodynlib" for configuration "Release"
set_property(TARGET aerodynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libaerodynlib.a"
  )

list(APPEND _cmake_import_check_targets aerodynlib )
list(APPEND _cmake_import_check_files_for_aerodynlib "${_IMPORT_PREFIX}/lib/libaerodynlib.a" )

# Import target "basicaerolib" for configuration "Release"
set_property(TARGET basicaerolib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(basicaerolib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libbasicaerolib.a"
  )

list(APPEND _cmake_import_check_targets basicaerolib )
list(APPEND _cmake_import_check_files_for_basicaerolib "${_IMPORT_PREFIX}/lib/libbasicaerolib.a" )

# Import target "aerodyn_driver_subs" for configuration "Release"
set_property(TARGET aerodyn_driver_subs APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodyn_driver_subs PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libaerodyn_driver_subs.a"
  )

list(APPEND _cmake_import_check_targets aerodyn_driver_subs )
list(APPEND _cmake_import_check_files_for_aerodyn_driver_subs "${_IMPORT_PREFIX}/lib/libaerodyn_driver_subs.a" )

# Import target "aerodyn_driver" for configuration "Release"
set_property(TARGET aerodyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/aerodyn_driver"
  )

list(APPEND _cmake_import_check_targets aerodyn_driver )
list(APPEND _cmake_import_check_files_for_aerodyn_driver "${_IMPORT_PREFIX}/bin/aerodyn_driver" )

# Import target "unsteadyaero_driver" for configuration "Release"
set_property(TARGET unsteadyaero_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(unsteadyaero_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/unsteadyaero_driver"
  )

list(APPEND _cmake_import_check_targets unsteadyaero_driver )
list(APPEND _cmake_import_check_files_for_unsteadyaero_driver "${_IMPORT_PREFIX}/bin/unsteadyaero_driver" )

# Import target "aerodyn_inflow_c_binding" for configuration "Release"
set_property(TARGET aerodyn_inflow_c_binding APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodyn_inflow_c_binding PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libaerodyn_inflow_c_binding.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libaerodyn_inflow_c_binding.dylib"
  )

list(APPEND _cmake_import_check_targets aerodyn_inflow_c_binding )
list(APPEND _cmake_import_check_files_for_aerodyn_inflow_c_binding "${_IMPORT_PREFIX}/lib/libaerodyn_inflow_c_binding.dylib" )

# Import target "adilib" for configuration "Release"
set_property(TARGET adilib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(adilib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libadilib.a"
  )

list(APPEND _cmake_import_check_targets adilib )
list(APPEND _cmake_import_check_files_for_adilib "${_IMPORT_PREFIX}/lib/libadilib.a" )

# Import target "aerodisklib" for configuration "Release"
set_property(TARGET aerodisklib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodisklib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libaerodisklib.a"
  )

list(APPEND _cmake_import_check_targets aerodisklib )
list(APPEND _cmake_import_check_files_for_aerodisklib "${_IMPORT_PREFIX}/lib/libaerodisklib.a" )

# Import target "aerodisk_driver" for configuration "Release"
set_property(TARGET aerodisk_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(aerodisk_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/aerodisk_driver"
  )

list(APPEND _cmake_import_check_targets aerodisk_driver )
list(APPEND _cmake_import_check_files_for_aerodisk_driver "${_IMPORT_PREFIX}/bin/aerodisk_driver" )

# Import target "servodynlib" for configuration "Release"
set_property(TARGET servodynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(servodynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libservodynlib.a"
  )

list(APPEND _cmake_import_check_targets servodynlib )
list(APPEND _cmake_import_check_files_for_servodynlib "${_IMPORT_PREFIX}/lib/libservodynlib.a" )

# Import target "servodyn_driver" for configuration "Release"
set_property(TARGET servodyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(servodyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/servodyn_driver"
  )

list(APPEND _cmake_import_check_targets servodyn_driver )
list(APPEND _cmake_import_check_files_for_servodyn_driver "${_IMPORT_PREFIX}/bin/servodyn_driver" )

# Import target "elastodynlib" for configuration "Release"
set_property(TARGET elastodynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(elastodynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libelastodynlib.a"
  )

list(APPEND _cmake_import_check_targets elastodynlib )
list(APPEND _cmake_import_check_files_for_elastodynlib "${_IMPORT_PREFIX}/lib/libelastodynlib.a" )

# Import target "beamdynlib" for configuration "Release"
set_property(TARGET beamdynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(beamdynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libbeamdynlib.a"
  )

list(APPEND _cmake_import_check_targets beamdynlib )
list(APPEND _cmake_import_check_files_for_beamdynlib "${_IMPORT_PREFIX}/lib/libbeamdynlib.a" )

# Import target "beamdyn_driver" for configuration "Release"
set_property(TARGET beamdyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(beamdyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/beamdyn_driver"
  )

list(APPEND _cmake_import_check_targets beamdyn_driver )
list(APPEND _cmake_import_check_files_for_beamdyn_driver "${_IMPORT_PREFIX}/bin/beamdyn_driver" )

# Import target "subdynlib" for configuration "Release"
set_property(TARGET subdynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(subdynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsubdynlib.a"
  )

list(APPEND _cmake_import_check_targets subdynlib )
list(APPEND _cmake_import_check_files_for_subdynlib "${_IMPORT_PREFIX}/lib/libsubdynlib.a" )

# Import target "subdyn_driver" for configuration "Release"
set_property(TARGET subdyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(subdyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/subdyn_driver"
  )

list(APPEND _cmake_import_check_targets subdyn_driver )
list(APPEND _cmake_import_check_files_for_subdyn_driver "${_IMPORT_PREFIX}/bin/subdyn_driver" )

# Import target "seastate_driver" for configuration "Release"
set_property(TARGET seastate_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(seastate_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/seastate_driver"
  )

list(APPEND _cmake_import_check_targets seastate_driver )
list(APPEND _cmake_import_check_files_for_seastate_driver "${_IMPORT_PREFIX}/bin/seastate_driver" )

# Import target "seastlib" for configuration "Release"
set_property(TARGET seastlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(seastlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libseastlib.a"
  )

list(APPEND _cmake_import_check_targets seastlib )
list(APPEND _cmake_import_check_files_for_seastlib "${_IMPORT_PREFIX}/lib/libseastlib.a" )

# Import target "seastate_c_binding" for configuration "Release"
set_property(TARGET seastate_c_binding APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(seastate_c_binding PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libseastate_c_binding.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libseastate_c_binding.dylib"
  )

list(APPEND _cmake_import_check_targets seastate_c_binding )
list(APPEND _cmake_import_check_files_for_seastate_c_binding "${_IMPORT_PREFIX}/lib/libseastate_c_binding.dylib" )

# Import target "hydrodynlib" for configuration "Release"
set_property(TARGET hydrodynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hydrodynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhydrodynlib.a"
  )

list(APPEND _cmake_import_check_targets hydrodynlib )
list(APPEND _cmake_import_check_files_for_hydrodynlib "${_IMPORT_PREFIX}/lib/libhydrodynlib.a" )

# Import target "hydrodyn_driver" for configuration "Release"
set_property(TARGET hydrodyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hydrodyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/hydrodyn_driver"
  )

list(APPEND _cmake_import_check_targets hydrodyn_driver )
list(APPEND _cmake_import_check_files_for_hydrodyn_driver "${_IMPORT_PREFIX}/bin/hydrodyn_driver" )

# Import target "hydrodyn_driver_subs" for configuration "Release"
set_property(TARGET hydrodyn_driver_subs APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hydrodyn_driver_subs PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhydrodyn_driver_subs.a"
  )

list(APPEND _cmake_import_check_targets hydrodyn_driver_subs )
list(APPEND _cmake_import_check_files_for_hydrodyn_driver_subs "${_IMPORT_PREFIX}/lib/libhydrodyn_driver_subs.a" )

# Import target "hydrodyn_c_binding" for configuration "Release"
set_property(TARGET hydrodyn_c_binding APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hydrodyn_c_binding PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhydrodyn_c_binding.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libhydrodyn_c_binding.dylib"
  )

list(APPEND _cmake_import_check_targets hydrodyn_c_binding )
list(APPEND _cmake_import_check_files_for_hydrodyn_c_binding "${_IMPORT_PREFIX}/lib/libhydrodyn_c_binding.dylib" )

# Import target "orcaflexlib" for configuration "Release"
set_property(TARGET orcaflexlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(orcaflexlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/liborcaflexlib.a"
  )

list(APPEND _cmake_import_check_targets orcaflexlib )
list(APPEND _cmake_import_check_files_for_orcaflexlib "${_IMPORT_PREFIX}/lib/liborcaflexlib.a" )

# Import target "orca_driver" for configuration "Release"
set_property(TARGET orca_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(orca_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/orca_driver"
  )

list(APPEND _cmake_import_check_targets orca_driver )
list(APPEND _cmake_import_check_files_for_orca_driver "${_IMPORT_PREFIX}/bin/orca_driver" )

# Import target "extptfm_mckflib" for configuration "Release"
set_property(TARGET extptfm_mckflib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(extptfm_mckflib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libextptfm_mckflib.a"
  )

list(APPEND _cmake_import_check_targets extptfm_mckflib )
list(APPEND _cmake_import_check_files_for_extptfm_mckflib "${_IMPORT_PREFIX}/lib/libextptfm_mckflib.a" )

# Import target "feamlib" for configuration "Release"
set_property(TARGET feamlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(feamlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libfeamlib.a"
  )

list(APPEND _cmake_import_check_targets feamlib )
list(APPEND _cmake_import_check_files_for_feamlib "${_IMPORT_PREFIX}/lib/libfeamlib.a" )

# Import target "feam_driver" for configuration "Release"
set_property(TARGET feam_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(feam_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/feam_driver"
  )

list(APPEND _cmake_import_check_targets feam_driver )
list(APPEND _cmake_import_check_files_for_feam_driver "${_IMPORT_PREFIX}/bin/feam_driver" )

# Import target "moordynlib" for configuration "Release"
set_property(TARGET moordynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(moordynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmoordynlib.a"
  )

list(APPEND _cmake_import_check_targets moordynlib )
list(APPEND _cmake_import_check_files_for_moordynlib "${_IMPORT_PREFIX}/lib/libmoordynlib.a" )

# Import target "moordyn_driver" for configuration "Release"
set_property(TARGET moordyn_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(moordyn_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/moordyn_driver"
  )

list(APPEND _cmake_import_check_targets moordyn_driver )
list(APPEND _cmake_import_check_files_for_moordyn_driver "${_IMPORT_PREFIX}/bin/moordyn_driver" )

# Import target "moordyn_c_binding" for configuration "Release"
set_property(TARGET moordyn_c_binding APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(moordyn_c_binding PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmoordyn_c_binding.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libmoordyn_c_binding.dylib"
  )

list(APPEND _cmake_import_check_targets moordyn_c_binding )
list(APPEND _cmake_import_check_files_for_moordyn_c_binding "${_IMPORT_PREFIX}/lib/libmoordyn_c_binding.dylib" )

# Import target "icedynlib" for configuration "Release"
set_property(TARGET icedynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(icedynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libicedynlib.a"
  )

list(APPEND _cmake_import_check_targets icedynlib )
list(APPEND _cmake_import_check_files_for_icedynlib "${_IMPORT_PREFIX}/lib/libicedynlib.a" )

# Import target "icefloelib" for configuration "Release"
set_property(TARGET icefloelib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(icefloelib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libicefloelib.a"
  )

list(APPEND _cmake_import_check_targets icefloelib )
list(APPEND _cmake_import_check_files_for_icefloelib "${_IMPORT_PREFIX}/lib/libicefloelib.a" )

# Import target "wdlib" for configuration "Release"
set_property(TARGET wdlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(wdlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libwdlib.a"
  )

list(APPEND _cmake_import_check_targets wdlib )
list(APPEND _cmake_import_check_files_for_wdlib "${_IMPORT_PREFIX}/lib/libwdlib.a" )

# Import target "awaelib" for configuration "Release"
set_property(TARGET awaelib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(awaelib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libawaelib.a"
  )

list(APPEND _cmake_import_check_targets awaelib )
list(APPEND _cmake_import_check_files_for_awaelib "${_IMPORT_PREFIX}/lib/libawaelib.a" )

# Import target "lindynlib" for configuration "Release"
set_property(TARGET lindynlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(lindynlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/liblindynlib.a"
  )

list(APPEND _cmake_import_check_targets lindynlib )
list(APPEND _cmake_import_check_files_for_lindynlib "${_IMPORT_PREFIX}/lib/liblindynlib.a" )

# Import target "mappplib" for configuration "Release"
set_property(TARGET mappplib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(mappplib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "C;CXX;Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libmappplib.a"
  )

list(APPEND _cmake_import_check_targets mappplib )
list(APPEND _cmake_import_check_files_for_mappplib "${_IMPORT_PREFIX}/lib/libmappplib.a" )

# Import target "extinflowtypeslib" for configuration "Release"
set_property(TARGET extinflowtypeslib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(extinflowtypeslib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libextinflowtypeslib.a"
  )

list(APPEND _cmake_import_check_targets extinflowtypeslib )
list(APPEND _cmake_import_check_files_for_extinflowtypeslib "${_IMPORT_PREFIX}/lib/libextinflowtypeslib.a" )

# Import target "extinflowlib" for configuration "Release"
set_property(TARGET extinflowlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(extinflowlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libextinflowlib.a"
  )

list(APPEND _cmake_import_check_targets extinflowlib )
list(APPEND _cmake_import_check_files_for_extinflowlib "${_IMPORT_PREFIX}/lib/libextinflowlib.a" )

# Import target "openfast_postlib" for configuration "Release"
set_property(TARGET openfast_postlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(openfast_postlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libopenfast_postlib.a"
  )

list(APPEND _cmake_import_check_targets openfast_postlib )
list(APPEND _cmake_import_check_files_for_openfast_postlib "${_IMPORT_PREFIX}/lib/libopenfast_postlib.a" )

# Import target "openfast_prelib" for configuration "Release"
set_property(TARGET openfast_prelib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(openfast_prelib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libopenfast_prelib.a"
  )

list(APPEND _cmake_import_check_targets openfast_prelib )
list(APPEND _cmake_import_check_files_for_openfast_prelib "${_IMPORT_PREFIX}/lib/libopenfast_prelib.a" )

# Import target "openfastlib" for configuration "Release"
set_property(TARGET openfastlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(openfastlib PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libopenfastlib.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libopenfastlib.dylib"
  )

list(APPEND _cmake_import_check_targets openfastlib )
list(APPEND _cmake_import_check_files_for_openfastlib "${_IMPORT_PREFIX}/lib/libopenfastlib.dylib" )

# Import target "sedlib" for configuration "Release"
set_property(TARGET sedlib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sedlib PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_RELEASE "Fortran"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsedlib.a"
  )

list(APPEND _cmake_import_check_targets sedlib )
list(APPEND _cmake_import_check_files_for_sedlib "${_IMPORT_PREFIX}/lib/libsedlib.a" )

# Import target "sed_driver" for configuration "Release"
set_property(TARGET sed_driver APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sed_driver PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/bin/sed_driver"
  )

list(APPEND _cmake_import_check_targets sed_driver )
list(APPEND _cmake_import_check_files_for_sed_driver "${_IMPORT_PREFIX}/bin/sed_driver" )

# Import target "wavetanktestinglib" for configuration "Release"
set_property(TARGET wavetanktestinglib APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(wavetanktestinglib PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libwavetanktestinglib.dylib"
  IMPORTED_SONAME_RELEASE "@rpath/libwavetanktestinglib.dylib"
  )

list(APPEND _cmake_import_check_targets wavetanktestinglib )
list(APPEND _cmake_import_check_files_for_wavetanktestinglib "${_IMPORT_PREFIX}/lib/libwavetanktestinglib.dylib" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
