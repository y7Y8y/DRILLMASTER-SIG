# Inventaire statique de la V1 — archive 2.9.394

Inventaire généré par lecture de l’archive extraite et analyse syntaxique Python. **Présence dans le code ≠ fonctionnalité active ou validée.** Les méthodes imbriquées ne sont pas toutes des points d’entrée utilisateur. Les imports indiqués sont directs ; cet inventaire ne prouve pas les chemins d’exécution. Les interfaces et scénarios doivent encore être observés sous QGIS.

## Fichiers Python

| Fichier | Lignes | Classes et fonctions de premier niveau | Dépendances internes directes (imports relatifs) |
|---|---:|---|---|
| `__init__.py` | 20 | classFactory (L10) | `.drillmaster` |
| `core/__init__.py` | 29 | — | `.csv_parser`, `.data_model`, `.geometry`, `.validation` |
| `core/about.py` | 114 | read_metadata (L63), about_info (L88), version_text (L111) | `.diagnostics` |
| `core/alteration_taxonomy.py` | 276 | _contains (L191), suggest_alteration_family (L199), suggest_alteration_pattern (L223), unicodedata_normalize (L272) | — |
| `core/assay_label_layout.py` | 140 | rects_intersect (L29), segment_hits_rect (L34), label_order (L58), _plan_once (L71), plan_end_labels (L113), stack_extent (L133) | — |
| `core/benchmark.py` | 192 | make_benchmark_drillholes (L52), bench_frame_render (L111), bench_surface_grid (L154), run_benchmark (L172) | `.camera3d`, `.data_model`, `.mesh_builder`, `.topography` |
| `core/camera3d.py` | 139 | OrbitCamera (L26) | — |
| `core/component_caps.py` | 48 | cap_for (L34), cap_excess (L39) | — |
| `core/crs_math.py` | 168 | parse_crs (L38), utm_to_wgs84 (L56), wgs84_to_utm (L105), conversion_between (L142) | — |
| `core/csv_parser.py` | 765 | levenshtein (L30), _normalise_header (L57), allowed_mapping (L105), sanitise_user_mappings (L110), _merged_synonyms (L118), fuzzy_match_header (L142), header_match_details (L177), detect_encoding (L226), detect_separator (L253), _count_outside_quotes (L287), detect_decimal_separator (L302), parse_number (L330), ParseResult (L385), parse_csv_file (L419), infer_lithology_structure (L578), find_delimited_values (L608), canonical_lithology_role (L629), normalise_editor_rows (L645), write_csv_file (L654), extract_validation_locations (L696), organisation_columns (L731), live_mapping_conflicts (L746) | `.data_model`, `.data_registry` |
| `core/data_model.py` | 543 | CollarRecord (L210), SurveyRecord (L223), StructureRecord (L232), CoreImageRecord (L287), GeotechRecord (L345), LithologyComponent (L412), IntervalRecord (L462), TrajectoryPoint (L496), DrillHole (L505) | — |
| `core/data_registry.py` | 219 | DatasetDefinition (L9), ComponentColumn (L61), ImportStructureProfile (L83), DataSourceRecord (L148), DataRegistry (L183) | — |
| `core/diagnostics.py` | 124 | _logger (L31), _QgisLogHandler (L45), log_swallowed (L68), log_warning (L84), record_timing (L104), timing_summary (L122) | — |
| `core/display_profiles.py` | 106 | infer_hole_type (L48), profile_for (L57), display_depth (L65), make_display_transform (L80) | — |
| `core/family_status.py` | 166 | FamilyStatus (L58), combine (L75), badge_count (L97), badge_rendu (L134) | — |
| `core/genesis_palettes.py` | 122 | family_base (L105), composite_stops (L112) | — |
| `core/geo_style.py` | 212 | kind_for_key (L80), profile_for_key (L101), ink_for_fill_hex (L114), ink_for_lightness (L128), StyleDefinition (L139), style_from_pattern (L171) | `.diagnostics`, `.reference` |
| `core/geometry.py` | 373 | _circular_mean_azimuth (L34), collar_info_text (L50), _compute_segment_displacement (L71), compute_trajectory (L93), validate_trajectory (L189), depth_to_xyz (L232), build_drillhole (L267), section_azimuth_degrees (L302), azimuth_label (L310), compass_needle (L315), section_rose_model (L342) | `.data_model` |
| `core/geometry_cache.py` | 143 | _from_dict (L42), _canonical (L47), geometry_signature (L71), cache_path (L75), save_geometry_cache (L79), load_geometry_cache (L107) | `.data_model`, `.diagnostics` |
| `core/geotech.py` | 350 | geotech_kind (L52), geotech_default_unit (L58), geotech_known_unit (L72), _value_of (L79), geotech_range (L99), geotech_legend_scale (L127), geotech_unit_for (L147), _lerp (L157), geotech_colour (L162), geotech_ramp_rgb (L203), geotech_label (L214), geotech_value_text (L223), geotech_depth_text (L233), geotech_anchor (L245), geotech_missing (L254), _interval_key (L267), geotech_rqd_over_recovery (L280), geotech_link_pairs (L318) | — |
| `core/i18n.py` | 194 | ts_path (L39), parse_ts (L44), available_languages (L77), load_language_setting (L82), save_language_setting (L99), install_translator (L111), set_language (L165), remove_translator (L185) | `.diagnostics` |
| `core/image_paths.py` | 67 | base_candidates (L13), _resolve_basename (L28), resolve_image_path (L41) | — |
| `core/import_detect.py` | 573 | detect_wide_component_columns (L171), FileTypeGuess (L280), FileSample (L304), read_header_sample (L315), _match_headers (L350), _numeric_fraction (L364), _numeric_extra_columns (L382), _gates_ok (L393), guess_file_type (L434), detect_file_type (L532), expand_dropped_paths (L543) | `.csv_parser` |
| `core/layers.py` | 1001 | get_or_create_root_group (L50), create_group_hierarchy (L60), _create_mem_layer (L84), _collar_fields (L98), _survey_fields (L114), _litho_fields (L120), _survey_station_fields (L137), _structure_fields (L148), _alteration_fields (L165), _mineralization_fields (L187), _assay_fields (L204), _ptz (L218), _linez (L223), _seg (L228), _add_feats (L237), _populate_collars (L242), _populate_survey (L260), _populate_survey_stations (L275), _populate_structure (L293), _populate_litho (L324), _populate_assays (L359), _domain_interval_codes (L378), _populate_alterations (L387), _populate_mineralizations (L425), _writer_result_status (L450), _save_to_gpkg (L468), setup_all_layers (L498), create_section_line_layer (L701), load_drillholes_from_gpkg (L723) | `.data_model`, `.diagnostics`, `.geometry`, `.section`, `.short_ids`, `.styles`, `.validation` |
| `core/lithology_taxonomy.py` | 213 | _contains (L160), nuance_to_family (L168), suggest_lithology_family (L191) | `.alteration_taxonomy` |
| `core/mesh_builder.py` | 153 | interpolate_dh_point (L29), segment_frame (L75), lane_point (L90), mineralization_style_codes (L99), interval_segments (L139) | — |
| `core/mineral_symbols.py` | 960 | P (L28), E (L32), L (L36), star_points (L40), _normalise_spec (L470), symbol_primitives (L488), _symbol_primitives (L500), shape_label_fr (L701), suggest_mineral_symbol (L726), to_core_symbol (L779), suggest_style_key (L861), legacy_symbol_to_style (L889), style_display_code (L898), legacy_pattern_to_style (L939) | — |
| `core/multi_assay.py` | 416 | hole_has_values (L23), numeric_fraction (L38), format_grade_value (L64), _canonical_unit (L110), _split_element_unit (L117), column_caption (L134), normalize_elements (L150), clamp_display_elements (L173), assay_selection_summary (L190), assay_legend_columns (L207), migrate_assay_style (L240), primary_element (L273), active_elements (L282), palette_for (L286), total_track_width (L295), sublane_layout (L308), collect_element_values (L345), build_scales (L364), style_snapshot_for_canvas (L402) | — |
| `core/organisation.py` | 151 | OrganisationQuestion (L42), delimited_examples (L65), organisation_question (L92), unconfirmed_wide_error_code (L143) | `.data_registry`, `.import_detect`, `.track_bands` |
| `core/pattern_paint.py` | 397 | _axis_frame (L30), _bounds_un (L38), _clamp (L46), _n_el (L50), _corners_from_rect (L57), _layout_geometry (L66), paint_style (L202), paint_style_swatch (L334), style_from_band (L381) | `.diagnostics`, `.geo_style`, `.reference` |
| `core/project.py` | 1143 | default_section_style (L26), default_assay_style (L138), default_config (L172), ProjectPaths (L256), DrillMasterProject (L279) | `.csv_parser`, `.data_model`, `.data_registry`, `.diagnostics`, `.mineral_symbols`, `.multi_assay`, `.reference`, `.section`, `.threshold_rule` |
| `core/reference.py` | 868 | distinct_auto_colors (L81), cycle_pattern_list (L117), normalise_pattern (L130), _hex_to_hsv (L191), _hsv_to_hex (L202), is_neutral_tone (L221), is_pastel_tone (L227), is_vivid_tone (L233), clamp_to_pastel (L242), clamp_to_vivid (L252), clamp_domain_color (L260), domain_color_palette (L274), automatic_code_color (L330), DomainEntry (L372), DomainDefinition (L418), ResolvedCategoryStyle (L449), automatic_display_label (L515), _suggest_element_metadata (L531), ReferenceRepository (L567), _apply_domain_suggestions (L807) | `.alteration_taxonomy`, `.diagnostics`, `.lithology_taxonomy`, `.mineral_symbols` |
| `core/scene3d/__init__.py` | 4 | — | `.geometry`, `.model` |
| `core/scene3d/adapter.py` | 185 | _lith_code (L25), _alter_code (L34), _num (L40), detect_assay_elements (L49), _hole_stations (L73), scene_from_drillholes (L98) | `.geometry`, `.model` |
| `core/scene3d/camera.py` | 100 | OrbitCamera (L13) | — |
| `core/scene3d/geometry.py` | 185 | build_trajectories (L15), positions (L57), SegmentBuffer (L69), interval_segments (L90), SpatialIndex (L115), build_spatial_index (L126), lod_selection (L142), expand_tubes (L164) | `.model` |
| `core/scene3d/model.py` | 74 | HoleTable (L26), IntervalTable (L45), SceneModel (L62) | — |
| `core/scene3d/render.py` | 307 | hex_to_rgb (L37), categorical_colors (L47), numeric_breaks (L59), numeric_colors (L68), RenderStyle (L80), Layer (L109), FrameStats (L118), RenderScene (L124), select_rows (L177), _raster (L202), render_frame (L239) | `.camera`, `.geometry`, `.model` |
| `core/scene3d/synthetic.py` | 117 | _intervals (L31), make_mine (L47) | `.geometry`, `.model` |
| `core/scene3d/zones.py` | 78 | detect_zones (L18), _name_zones (L58) | — |
| `core/section.py` | 1047 | SectionLine (L34), compass16 (L121), _azimuth_to_compass (L128), ProjectedPoint (L136), ProjectedInterval (L147), ProjectedStructure (L164), ProjectedHole (L186), SectionResult (L211), compute_isotropic_scales (L239), grid_tick_values (L246), _nice_step (L255), depth_tick_steps (L271), project_point_onto_section (L292), point_to_section_segment_distance (L308), drillhole_buffer_status (L318), group_shared_collars (L375), compute_buffer_diagnostics (L398), generate_section (L411), _project_structures (L601), _project_intervals (L637), _finite_numbers (L693), jenks_breaks (L700), adaptive_break_step (L753), round_jenks_breaks (L767), compute_assay_scale (L788), classify_assay (L850), assay_scale_classes (L888), _interpolate_rgb (L928), assay_ramp_rgb (L932), generated_litho_color (L951), suggested_litho_color (L969), get_litho_style (L1003), get_litho_color (L1025), get_all_litho_codes (L1029) | `.data_model`, `.display_profiles`, `.geometry`, `.lithology_taxonomy`, `.topography` |
| `core/section_scale.py` | 97 | unit_factor (L26), sx_for_ratio (L30), ratio_from_sx (L35), nice_step (L40), grid_step_for_ratio (L55), common_elev_window (L67), auto_project_ratio (L87) | — |
| `core/selection_model.py` | 168 | IntervalSelection (L17), EntitySelection (L104) | — |
| `core/short_ids.py` | 53 | trailing_number (L22), label_width (L28), compact_label (L34), compact_labels (L42) | — |
| `core/spatial_model.py` | 288 | SpatialCoordinateSystem (L33), SpatialModel (L45) | `.data_model`, `.geometry`, `.selection_model` |
| `core/step3_summary.py` | 58 | _tr (L19), build_step3_summary (L30) | — |
| `core/structure_analysis.py` | 406 | StructureSample (L33), Orientation (L52), RoseBin (L60), _has_dip_pair (L69), _has_alpha_beta_pair (L76), sample_family (L83), plane_strike (L90), is_alpha_beta_only (L101), resolve_orientation (L106), rose_value (L137), rose_index (L159), rose_bins (L180), project_schmidt (L213), filter_structure_samples (L239), sample_codes (L265), collect_samples_from_holes (L271), analysis_counts (L296), pole_density_grid (L336) | `.structure_classify` |
| `core/structure_classify.py` | 214 | _normalize (L180), _contains_any (L184), structure_family (L191), orientation_expected (L212) | — |
| `core/style_resolver.py` | 177 | StyleResolver (L47) | `.diagnostics`, `.mineral_symbols`, `.reference`, `.section` |
| `core/styles.py` | 388 | _gtype_point (L8), _gtype_line (L12), _circle (L16), create_collar_style (L25), create_survey_style (L41), pattern_min_marks (L90), pattern_mark_geometry (L108), tube_pattern_render (L156), line_dash_pattern (L172), create_litho_style (L186), create_domain_style (L230), create_structure_style (L270), create_assay_style (L318), create_section_line_style (L377) | `.reference`, `.section` |
| `core/threshold_rule.py` | 809 | rule_color_for_index (L47), _normalize_color_hex (L58), color_name_for_hex (L76), _normalize_litho_filter (L85), _parse_clause_value (L117), _normalize_clause (L126), _normalize_clauses (L142), normalize_rule (L176), is_active (L226), empty_rule (L231), normalize_rules (L236), migrate_threshold_payload (L269), intercept_lane_offsets (L297), active_rules (L314), legend_labels_multi (L319), compare (L339), clause_value_ok (L351), clause_matches (L370), _litho_codes_for_interval (L386), litho_filter_matches (L415), interval_matches (L428), _as_numeric (L477), _iter_assay_attribute_maps (L495), collect_element_values (L512), element_value_range (L531), outline_draw_elements (L539), intercept_track_wanted (L574), intercept_track_width (L579), intercept_slot_layout (L594), anchor_element (L636), explain_match (L645), operator_label (L688), group_contiguous_matches (L697), _legend_element_name (L749), legend_label (L765) | `.diagnostics`, `.multi_assay` |
| `core/topography.py` | 772 | _finite (L50), profile_at (L54), profile_from_collars (L76), collar_deviations (L109), _decay_length (L141), anchor_profile_to_collars (L150), densify_profile (L245), smooth_profile (L285), refine_surface_profile (L320), merge_surface_into_range (L350), bounds_from_points (L380), _idw_z (L408), build_surface_grid (L438), grid_from_gridded_samples (L473), smooth_surface_grid (L524), grid_z_at (L574), _grid_decay_length (L603), anchor_grid_to_collars (L615), _march_cell (L676), contour_segments (L714), contour_levels (L741) | — |
| `core/track_bands.py` | 347 | BandSpec (L70), looks_like_vein (L96), draw_role (L112), _role_and_proportion (L128), component_band_layout (L148), reduced_rail_fraction (L250), lane_slots (L279), intensity_factor (L309), split_delimited_codes (L338) | — |
| `core/track_layout.py` | 746 | _sign (L52), depth_lane_width (L56), estimated_depth_label_width (L66), scene_normal (L72), pattern_rotation_degrees (L85), depth_label_base (L99), depth_tick_segment (L108), TrackLane (L135), TrackPlan (L157), plan_tracks (L168), band_polygon (L235), rightward_normal (L272), band_trapezoid (L287), diagonal_filet_polygon (L316), stick_polygon (L350), band_edge_x (L373), band_horizontal_room (L387), angled_depot_candidates (L395), label_rotation_degrees (L454), first_free_slot (L472), first_free_position (L496), rotated_aabb (L518), code_fits (L538), elide_code (L550), fit_font_size (L569), fit_code_to_band (L591), obb_intersects (L622), label_rect_free (L669), zone_inset_frame (L686), mini_section_points (L696), zone_inset_project (L706) | — |
| `core/ui_audit.py` | 72 | UiAuditIssue (L10), audit_ui_connections (L17) | — |
| `core/validation.py` | 2134 | ValidationIssue (L26), ValidationResult (L72), ImportBundle (L125), _basename (L145), _column_indexes (L149), _header_index (L158), _source_line (L171), _message_prefix (L175), _check_mapping_safety (L179), _cell (L269), _parse_numeric (L273), _collar_ids_and_depths (L298), _hole_similarity_warnings (L311), validate_collar (L332), validate_survey (L415), validate_structure (L565), _is_image_file (L763), validate_imagery (L768), validate_geotech (L891), validate_geotech_cross (L1115), _parse_proportion (L1149), _component (L1180), validate_lithology (L1211), validate_intervals (L1555), _find_qaqc_column (L2094), _classify_assay_value (L2115), auto_survey_for_vertical (L2129) | `.component_caps`, `.csv_parser`, `.data_model`, `.geotech`, `.import_detect`, `.organisation`, `.structure_classify`, `.track_bands` |
| `core/validation_groups.py` | 276 | IssueGroup (L110), _group_key (L136), group_issues (L145), filter_by_severity (L181), cap_groups (L188), count_by_severity (L203), normalise_severity (L234), show_info_lines (L241), overflow_summary (L246), filter_labels (L265) | — |
| `core/workspace.py` | 169 | WorkspaceState (L10) | `.diagnostics`, `.selection_model` |
| `drillmaster.py` | 413 | _tr (L20), _read_plugin_version (L29), _schedule_splash_close (L43), DrillMasterPlugin (L79) | `.core.diagnostics`, `.core.i18n`, `.core.workspace`, `.ui.about_dialog`, `.ui.main_dock`, `.ui.splash`, `.ui.visualization_dock` |
| `tools/bench_qpainter_draw.py` | 61 | make_scene (L20), bench (L36) | — |
| `tools/bench_scene3d.py` | 51 | mb (L10), run (L12) | — |
| `tools/test_assay_label_layout.py` | 62 | rightward_normal (L5) | — |
| `tools/test_common_scale.py` | 41 | VP (L26), mk (L29) | — |
| `tools/test_default_scale.py` | 48 | hole (L14), mk (L20), metrics (L30) | — |
| `tools/test_elev_window.py` | 54 | hole (L17), sr (L22), mk (L23) | — |
| `tools/test_window_room.py` | 46 | Pt (L19), dh (L21), mk (L27) | — |
| `ui/__init__.py` | 1 | — | — |
| `ui/about_dialog.py` | 234 | AboutDialog (L31), make_about_icon (L227) | `..core.about`, `.styles_qt` |
| `ui/csv_editor.py` | 573 | CsvEditorDialog (L25) | `..core.csv_parser`, `.styles_qt`, `.validation_i18n` |
| `ui/display_profiles_dialog.py` | 244 | DisplayProfilesDialog (L21), attach_hole_type_row (L84), attach_surface_anchor_row (L131), attach_common_scale_row (L167) | `..core.section_scale` |
| `ui/domain_structure_dialog.py` | 220 | DomainStructureDialog (L32) | `..core.component_caps`, `..core.data_registry`, `..core.import_detect`, `.styles_qt` |
| `ui/lithology_structure_dialog.py` | 365 | LithologyStructureDialog (L17) | `..core.component_caps`, `..core.data_registry`, `.styles_qt` |
| `ui/main_dock.py` | 1457 | compute_auto_trajectories (L36), _TrajWorker334 (L72), MainDock (L95) | `..core.data_model`, `..core.diagnostics`, `..core.geometry`, `..core.geometry_cache`, `..core.i18n`, `..core.layers`, `..core.project`, `..core.reference`, `..core.section`, `..core.styles`, `..core.validation`, `..core.workspace`, `.about_dialog`, `.display_profiles_dialog`, `.reference_dialog`, `.step1_config`, `.step2_import`, `.step3_geometry`, `.step4_section`, `.stepper`, `.styles_qt` |
| `ui/overlay_layout.py` | 59 | _overlap (L23), overlay_layout (L29) | — |
| `ui/raster_surface.py` | 496 | _tr (L37), csv_topography_points (L47), qgis_raster_layers (L111), _extract_value (L129), _bilinear_at (L208), raster_block_dims (L249), sample_raster_grid (L280) | `..core.crs_math`, `..core.csv_parser`, `..core.diagnostics` |
| `ui/reference_dialog.py` | 1132 | _pattern_icon (L47), _DomainColorPicker (L82), ReferenceDialog (L168) | `..core.diagnostics`, `..core.mineral_symbols`, `..core.reference`, `..core.section`, `.styles_qt` |
| `ui/section_dock.py` | 11529 | _selection_highlight_pen (L872), _selection_chrome_stylesheet (L889), _pattern_ink_colour (L932), _export_smallcaps_font (L944), _export_sc_text (L958), _legend_label (L966), CollapsibleGroup (L994), _PatternPolygonItem (L1058), _ClippedStrokeItem (L1074), _ClippedFillItem (L1114), _StyledFillItem (L1144), SectionCanvas (L1191), SectionWidget (L6234) | `..core`, `..core.alteration_taxonomy`, `..core.assay_label_layout`, `..core.crs_math`, `..core.data_model`, `..core.diagnostics`, `..core.display_profiles`, `..core.genesis_palettes`, `..core.geometry`, `..core.mineral_symbols`, `..core.multi_assay`, `..core.pattern_paint`, `..core.project`, `..core.reference`, `..core.section`, `..core.section_scale`, `..core.short_ids`, `..core.topography`, `..core.track_bands`, `..core.track_layout`, `.display_profiles_dialog`, `.section_export`, `.section_export_scaled`, `.section_geotech`, `.section_holes`, `.section_imagery`, `.section_structure`, `.section_surface`, `.styles_qt` |
| `ui/section_export.py` | 2174 | _tr (L44), export_view_png (L51), run_deferred_export (L108), _LocPreview (L168), export_png_dialog (L195), export_scene_rect (L381), crop_white_margins (L406), grab_legends_image (L478), paint_legends_image (L482), paint_legends_image_impl (L493), export_domain_codes (L1277), export_meta_dict (L1296), paint_export_title (L1341), paint_export_footer (L1378), paint_export_cartouche (L1421), paint_locator_map (L1425), compose_export_page (L1725), stamp_locator_on_section (L1829), render_canvas_to_png (L1879), get_svg_generator_class (L2148), render_canvas_to_svg (L2171) | `..core`, `..core.diagnostics`, `..core.mineral_symbols`, `..core.section`, `..core.structure_classify`, `.section_dock`, `.section_imagery`, `.styles_qt` |
| `ui/section_export_scaled.py` | 621 | _tr (L58), unit_factor (L63), sx_for_scale (L67), page_size (L72), Layout (L80), plan_layout (L93), fits_area (L148), effective_dpi (L153), nice_ratio (L162), _draw_fit (L169), compose_scaled_page (L177), save_page (L265), _cartouche_images (L292), _natural_mm (L314), _locator_mm (L322), _title_footer (L329), run_scaled_export (L347), export_scaled_dialog (L482) | `..core.diagnostics`, `.section_export` |
| `ui/section_geotech.py` | 553 | _attr (L51), has_data (L55), geotech_track_spec (L66), geotech_tooltip (L86), draw_geotech (L104), _anchor_points (L163), _draw_density_line (L180), _draw_interval_band (L208), _draw_point_marker (L234), _draw_missing_band (L262), build_geotech_group (L290), read_geotech_style (L372), apply_geotech_style_to_widget (L395), _legend_swatch (L422), create_legend_widgets (L427), refresh_geotech_legend (L453), init_geotech_defaults (L493), geotech_display_attrs (L507), geotech_track_pages (L520), geotech_track_tips (L531), add_geotech_legends (L543), refresh_all_geotech_legends (L549) | `..core.diagnostics`, `..core.geotech`, `..core.track_bands`, `..core.track_layout`, `.styles_qt` |
| `ui/section_holes.py` | 377 | _tr (L37), hole_id_at (L49), canvas_context_menu (L104), _auto_expand_inclusion (L149), set_excluded (L160), exclude_hole (L180), include_hole (L185), include_all (L190), restore_for_section (L195), parse_record (L204), build_hole_filter_row (L219), _toggle_list (L266), _on_item_changed (L275), refresh_hole_filter_ui (L285), _corridor_holes (L320), legend_source_holes (L344), sync_hole_type_combo (L358) | `..core.diagnostics`, `..core.section`, `.styles_qt` |
| `ui/section_imagery.py` | 760 | ImageryPixmapCache (L77), _canvas_cache (L193), has_data (L210), imagery_source_dir (L214), imagery_project_and_source (L227), imagery_track_spec (L237), _material_text (L250), imagery_tooltip (L259), _affine_for_pixmap (L290), _composite_band_pixmap (L314), _draw_hatched_missing (L368), _material_badge_letter (L399), _draw_material_badge (L404), _draw_image_item (L458), draw_imagery (L505), build_imagery_group (L543), open_imagery_assets (L613), _legend_label (L638), create_legend_widgets (L654), fill_imagery_legend (L672), refresh_imagery_legend (L717), update_legend_visibility (L726), read_imagery_style (L739), apply_imagery_style_to_widget (L753) | `..core.data_model`, `..core.diagnostics`, `..core.image_paths`, `.styles_qt` |
| `ui/section_structure.py` | 675 | structure_click_target (L31), apply_structure_click (L50), highlight_structure_point (L80), _legend_label (L117), draw_structures (L136), _section_bearing (L235), _scene_dip_vector (L247), _draw_marker (L267), _draw_planar_tadpole (L279), _draw_linear_arrow (L297), structure_tooltip (L326), build_structure_group (L348), _legend_structure_pixmap (L441), fill_structure_legend (L489), has_data (L536), track_spec (L541), update_legend_visibility (L552), open_structure_analysis (L563), create_legend_widgets (L622), read_structure_style (L640), apply_structure_style_to_widget (L661) | `..core.diagnostics`, `..core.structure_analysis`, `..core.structure_classify`, `..core.track_bands`, `..core.track_layout`, `.section_holes`, `.structure_analysis_dialog`, `.styles_qt` |
| `ui/section_surface.py` | 848 | _tr (L25), qgis_raster_layers (L34), surface_raster_layer (L76), extract_raster_sample (L97), sample_raster_along_line (L195), topography_csv_path (L484), topography_csv_points (L493), surface_provider (L547), surface_tooltip_text (L662), update_surface_status (L697), update_surface_detection_status (L747), on_surface_source_change (L785), on_surface_qc_change (L803), refresh_surface_combo (L814), populate_surface_combo (L828) | `..core.crs_math`, `..core.csv_parser`, `..core.diagnostics`, `..core.section`, `..core.topography`, `.styles_qt` |
| `ui/splash.py` | 207 | PluginSplash (L36), make_splash (L197) | `..core.diagnostics` |
| `ui/step1_config.py` | 315 | Step1Config (L20) | `..core.diagnostics`, `..core.i18n`, `..core.project`, `.styles_qt` |
| `ui/step2_import.py` | 2860 | DropZone (L156), _tr (L257), _validation_group_translate (L264), _validation_english_mode (L274), _regex_from_template (L319), _translate_parse_message (L343), _preview_hint_text (L360), ImportTab (L371), GroupedValidationPanel (L1485), FamilyChip (L1754), Step2Import (L1831) | `..core.component_caps`, `..core.csv_parser`, `..core.data_model`, `..core.data_registry`, `..core.diagnostics`, `..core.family_status`, `..core.i18n`, `..core.import_detect`, `..core.multi_assay`, `..core.organisation`, `..core.track_bands`, `..core.validation`, `..core.validation_groups`, `.csv_editor`, `.domain_structure_dialog`, `.lithology_structure_dialog`, `.styles_qt` |
| `ui/step3_geometry.py` | 352 | GeometrisationTask (L21), Step3Geometry (L67) | `..core.data_model`, `..core.diagnostics`, `..core.geometry`, `..core.geometry_cache`, `..core.step3_summary`, `..core.validation`, `.styles_qt` |
| `ui/step4_section.py` | 397 | SectionMapTool (L20), Step4Section (L95) | `..core.diagnostics`, `..core.section`, `.styles_qt` |
| `ui/stepper.py` | 118 | StepIndicator (L17), StepperWidget (L53) | — |
| `ui/structure_analysis_dialog.py` | 913 | _StructureRoseWidget (L76), _StructureStereonetWidget (L170), StructureAnalysisDialog (L553) | `..core.diagnostics`, `..core.structure_analysis`, `.styles_qt` |
| `ui/styles_qt.py` | 577 | apply_combo_popup_style (L329), suppress_button_focus_rects (L510), make_collapsible_help (L539) | `..core.diagnostics` |
| `ui/validation_i18n.py` | 112 | validation_english_mode (L34), validation_translate (L39), validation_label (L45), validation_issue_text (L60), validation_issue_tooltip (L80), _first_row (L104) | `..core.i18n`, `..core.validation_groups` |
| `ui/view_3d.py` | 479 | View3DWidget (L33) | `..core.diagnostics`, `..core.multi_assay`, `..core.spatial_model`, `..core.workspace`, `.raster_surface`, `.styles_qt`, `.view_3d_canvas`, `.view_3d_dialogs`, `.view_3d_panel`, `.view_3d_surface` |
| `ui/view_3d_async.py` | 142 | _CanvasProxy (L38), SceneRenderWorker (L83) | `..core.diagnostics`, `.view_3d_renderer` |
| `ui/view_3d_canvas.py` | 1523 | _tr (L59), View3DCanvas (L93) | `..core.camera3d`, `..core.data_model`, `..core.diagnostics`, `..core.mesh_builder`, `..core.multi_assay`, `..core.section`, `..core.selection_model`, `..core.spatial_model`, `..core.style_resolver`, `..core.threshold_rule`, `..core.topography`, `..core.track_bands`, `..core.workspace`, `.styles_qt`, `.view_3d_interaction`, `.view_3d_overlays`, `.view_3d_renderer` |
| `ui/view_3d_dialogs.py` | 117 | _AssayElementDialog (L19) | — |
| `ui/view_3d_imagery_viewer.py` | 276 | _load_photo_any_size (L35), _filename_depth_ranges (L82), _imagery_source_dir (L115), _ImageryPhotoDialog (L125), show_imagery_photo (L268) | `..core.diagnostics`, `..core.image_paths` |
| `ui/view_3d_interaction.py` | 222 | mouse_press (L19), mouse_move (L35), mouse_release (L78), wheel (L92), _ref_point (L107), find_hover_tooltip (L119), handle_click_selection (L145) | `.view_3d_imagery_viewer` |
| `ui/view_3d_overlays.py` | 912 | _tr (L26), _imagery_material_label (L32), _imagery_badge_color (L41), _imagery_legend_entries (L77), elide_text (L109), _geotech_legend_columns (L123), _multi_domain_group_columns (L161), _draw_multi_domain_legend (L261), _draw_legend_pattern (L424), _draw_structure_legend_swatch (L479), draw_floating_legend (L530), draw_gizmo (L773), draw_exag_badge (L799), _wrap_tooltip_lines (L818), draw_hover_tooltip (L848) | `..core.diagnostics`, `..core.geotech`, `..core.multi_assay`, `..core.section`, `..core.structure_classify`, `..core.styles`, `..core.threshold_rule`, `.overlay_layout`, `.section_imagery`, `.view_3d_renderer` |
| `ui/view_3d_panel.py` | 373 | _tr (L22), build_side_panel (L30) | `..core.multi_assay`, `.styles_qt` |
| `ui/view_3d_renderer.py` | 2614 | _tr (L38), _in_motion (L44), _scene_cache_key (L62), _blit_cached (L126), _async_ok (L152), _start_async_render (L173), _on_scene_ready (L190), paint_scene (L218), _emit_render_status (L285), _aa_layer (L308), _safe_layer (L330), _render_scene (L349), draw_topography_surface (L483), draw_bounding_box (L667), draw_section_plane_and_corridor (L797), _pattern_tube_marks (L866), _cached_pen (L953), _frame_lane_direction (L989), _draw_component_bands (L1015), _draw_intercept_sleeves (L1105), _selection_dim (L1163), _structure_world_dip_vector (L1229), _structure_tooltip (L1247), _structure_hole_normal (L1276), _draw_structure_marker (L1302), draw_structure_markers (L1383), draw_geotech_3d (L1490), _imagery_3d_source_dir (L1591), _draw_imagery_badge (L1609), _imagery_file_present (L1652), _imagery_secondary_offset (L1681), _draw_imagery_strips (L1716), _imagery_label_clear (L1797), _short_label (L1817), draw_drillhole (L1829), _draw_assay_marker (L2469), _draw_element_key (L2484), draw_assay_bubble (L2518), draw_selection_highlight (L2565) | `..core.data_model`, `..core.diagnostics`, `..core.geotech`, `..core.image_paths`, `..core.mesh_builder`, `..core.multi_assay`, `..core.short_ids`, `..core.structure_classify`, `..core.styles`, `..core.threshold_rule`, `..core.topography`, `..core.track_bands`, `.section_imagery`, `.styles_qt`, `.view_3d_async` |
| `ui/view_3d_surface.py` | 231 | _tr (L18), section_mnt_choice (L23), compute_surface_grid (L44) | `..core.diagnostics`, `..core.topography`, `.raster_surface` |
| `ui/view_3d_v2.py` | 712 | _BuildThread (L35), _Viewport (L54), View3DV2 (L127) | `..core.multi_assay`, `..core.scene3d.adapter`, `..core.scene3d.camera`, `..core.scene3d.render`, `..core.scene3d.zones` |
| `ui/visualization_dock.py` | 375 | _view3d_enabled (L28), VisualizationDock (L36) | `..core.diagnostics`, `.section_dock`, `.styles_qt`, `.view_3d_v2` |

## Autres fichiers de l’archive

| Chemin | Taille octets |
|---|---:|
| `LICENSE` | 17983 |
| `bibliotheques/bibliotheque_alteration.csv` | 5542 |
| `bibliotheques/bibliotheque_lithologie.csv` | 5046 |
| `i18n/drillmaster_en.ts` | 383296 |
| `i18n/drillmaster_fr.ts` | 409 |
| `icon.png` | 3736 |
| `metadata.txt` | 777 |
| `palettes/alt_palette.json` | 4565 |
| `palettes/litho_palette.json` | 4921 |
| `palettes/palette_geologique.html` | 21507 |

## Portée et suite

Ce relevé couvre tous les fichiers présents dans l’archive, non les ressources produites à l’exécution ni les dépendances externes. Il ne remplace pas une analyse de toutes les fonctions, des appels dynamiques ou des dialogues créés en cours d’exécution. Utiliser avec `diagnostic-initial.md` et compléter par un registre de scénarios observés en environnement QGIS.

## Fiches d’interface — relevé syntaxique complémentaire

Méthode : classes héritant directement des bases Qt/QGIS listées et fonctions créant explicitement un `QDialog`. Les compteurs sont des appels présents dans la portée syntaxique, **pas** des contrôles visibles simultanément. Ils incluent le code conditionnel et excluent les widgets construits par des fonctions externes. Les dialogues natifs (QMessageBox, QFileDialog, QColorDialog et autres), fabriques, héritages indirects et interfaces déclenchées dynamiquement peuvent manquer ; registre à compléter pendant l’exécution. L’absence de métrique ne prouve pas l’absence de risque. État commun : non observé en QGIS ; apparence, accès et clavier non validés.

### `about_dialog.py:31` — `AboutDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QLabel ×11, QVBoxLayout ×2, QHBoxLayout ×2, QDialogButtonBox ×1, QFrame ×1, QWidget ×1, QPixmap ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('À propos de DrillMaster')) L38; setMinimumWidth(470) L39; setFixedSize(48, 48) L56; setFixedHeight(1) L196; setMinimumWidth(190) L212.
- Événements directs (dix premiers maximum) : buttons.rejected.connect L186; buttons.accepted.connect L187.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `csv_editor.py:25` — `CsvEditorDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QBrush ×6, QColor ×6, QPushButton ×4, QLabel ×3, QTableWidgetItem ×3, QVBoxLayout ×2, QHBoxLayout ×2, QTimer ×1, QCheckBox ×1, QSplitter ×1, QTableWidget ×1, QWidget ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Éditeur CSV — {}').format(file_name)) L55; resize(1100, 700) L56.
- Événements directs (dix premiers maximum) : self._validation_timer.timeout.connect L47; self.errors_only.stateChanged.connect L82; self.table.itemChanged.connect L102; self.error_list.itemClicked.connect L111; self.save_project_btn.clicked.connect L125; self.save_as_btn.clicked.connect L129; close_btn.clicked.connect L133; button.clicked.connect L141.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `display_profiles_dialog.py:21` — `DisplayProfilesDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QCheckBox ×3, QLabel ×2, QVBoxLayout ×1, QComboBox ×1, QDialogButtonBox ×1.
- Dimensions / titres directs : setWindowTitle(self.tr("Profils d'affichage par type d'ouvrage")) L27.
- Événements directs (dix premiers maximum) : buttons.accepted.connect L64; buttons.rejected.connect L65.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `domain_structure_dialog.py:32` — `DomainStructureDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QComboBox ×3, QFormLayout ×3, QWidget ×3, QVBoxLayout ×2, QStackedWidget ×1, QListWidget ×1, QLineEdit ×1, QDialogButtonBox ×1, QLabel ×1, QListWidgetItem ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Organisation — {}').format(self.domain_label)) L49; resize(560, 420) L50.
- Événements directs (dix premiers maximum) : self.mode_combo.currentIndexChanged.connect L68; buttons.accepted.connect L135; buttons.rejected.connect L136.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `lithology_structure_dialog.py:17` — `LithologyStructureDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QComboBox ×5, QLabel ×4, QWidget ×4, QHBoxLayout ×3, QVBoxLayout ×2, QFormLayout ×2, QPushButton ×2, QStackedWidget ×1, QDialogButtonBox ×1, QTableWidget ×1, QLineEdit ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Organisation des lithologies')) L61; resize(720, 470) L62.
- Événements directs (dix premiers maximum) : self.mode_combo.currentIndexChanged.connect L78; buttons.accepted.connect L115; buttons.rejected.connect L116; add.clicked.connect L178; remove.clicked.connect L183; self.delimiter.textChanged.connect L208; self.delimited_code.currentIndexChanged.connect L209.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `main_dock.py:95` — `MainDock`

- Nature : classe, bases QgsDockWidget.
- Composants repérés : QVBoxLayout ×4, QLabel ×4, QColor ×3, QWidget ×2, QFrame ×2, QHBoxLayout ×2, QToolButton ×2, QPushButton ×2, QRadioButton ×2, QSettings ×2, QTabWidget ×1, QMenu ×1.
- Dimensions / titres directs : setMinimumWidth(340) L126; setWindowTitle(self.tr('Réinitialiser le projet')) L675; setWindowTitle(self.tr('Suppression définitive')) L708; setWindowTitle(_QCA.translate('MainDock', 'DrillMaster — Contrôle · Données & Coupes')) L1277.
- Événements directs (dix premiers maximum) : QgsProject.instance().layersWillBeRemoved.connect L122; self.about_button.clicked.connect L172; self.reference_action.triggered.connect L185; self.profiles_action.triggered.connect L192; self.close_project_action.triggered.connect L198; self.reset_project_action.triggered.connect L206; self.btn_prev.clicked.connect L255; self.btn_next.clicked.connect L260; self.step1.validity_changed.connect L273; self.step2.validity_changed.connect L274.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `reference_dialog.py:82` — `_DomainColorPicker`

- Nature : classe, bases QDialog.
- Composants repérés : QColor ×2, QVBoxLayout ×1, QScrollArea ×1, QWidget ×1, QGridLayout ×1, QLabel ×1, QDialogButtonBox ×1, QPushButton ×1.
- Dimensions / titres directs : setWindowTitle(title) L99; setMinimumWidth(420) L100; setMinimumHeight(36) L139; setFixedSize(34, 28) L122.
- Événements directs (dix premiers maximum) : buttons.accepted.connect L144; buttons.rejected.connect L145; btn.clicked.connect L131.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `reference_dialog.py:168` — `ReferenceDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QColor ×9, QBrush ×5, QComboBox ×4, QPushButton ×4, QHBoxLayout ×3, QLabel ×3, QLineEdit ×2, QVBoxLayout ×1, QTableWidget ×1, QGroupBox ×1, QFormLayout ×1, QDoubleSpinBox ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Référentiel du projet — v{}').format(REFERENCE_VERSION)) L239; resize(1080, 650) L241; setMinimumSize(760, 480) L242; setWindowTitle(self.tr('Couleur de {}').format(code_label)) L804.
- Événements directs (dix premiers maximum) : self.domain_combo.currentIndexChanged.connect L255; self.search_edit.textChanged.connect L261; self.status_filter.currentIndexChanged.connect L271; self.table.cellDoubleClicked.connect L285; self.table.currentCellChanged.connect L286; self.details.toggled.connect L314; self.reset_button.clicked.connect L324; self.cleanup_button.clicked.connect L329; self.auto_patterns_button.clicked.connect L341; self.auto_colors_button.clicked.connect L354.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_dock.py:994` — `CollapsibleGroup`

- Nature : classe, bases QWidget.
- Composants repérés : QVBoxLayout ×1, QToolButton ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : self.header.toggled.connect L1037.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_dock.py:1191` — `SectionCanvas`

- Nature : classe, bases QGraphicsView.
- Composants repérés : QColor ×72, QPen ×36, QPointF ×29, QBrush ×23, QFont ×18, QRectF ×12, QPolygonF ×10, QPainterPath ×7, QFontMetrics ×4, QPainterPathStroker ×2, QLinearGradient ×2, QTransform ×2.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_dock.py:6234` — `SectionWidget`

- Nature : classe, bases QWidget.
- Composants repérés : QLabel ×30, QCheckBox ×23, QComboBox ×22, QWidget ×21, QColor ×20, QVBoxLayout ×17, QDoubleSpinBox ×17, QSpinBox ×14, QHBoxLayout ×12, QFormLayout ×12, QPen ×12, QBrush ×12.
- Dimensions / titres directs : setMinimumWidth(120) L6314; setMinimumWidth(0) L6335; setMinimumHeight(84) L7037; setMinimumWidth(32) L7968; setFixedSize(24, 14) L10553; setFixedSize(24, 14) L10579; setFixedSize(24, 14) L10604; setFixedSize(24, 14) L10635; setFixedSize(16, 16) L7724; setFixedSize(28, 16) L10441.
- Événements directs (dix premiers maximum) : self._geometry_timer.timeout.connect L6270; self._style_timer.timeout.connect L6275; self._exag_timer.timeout.connect L6279; self._persist_timer.timeout.connect L6283; self._legends_timer.timeout.connect L6287; self.canvas.rendered.connect L6329; self.track_list.itemClicked.connect L6553; self.track_list.itemChanged.connect L6557; self.section_combo.currentIndexChanged.connect L7000; self.section_table.itemClicked.connect L7043.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_export.py:168` — `_LocPreview`

- Nature : classe, bases QLabel.
- Composants repérés : aucun constructeur Qt direct.
- Dimensions / titres directs : setFixedSize(190, 208) L178.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_export.py:195` — `export_png_dialog`

- Nature : fabrique de dialogue.
- Composants repérés : QLabel ×5, QHBoxLayout ×4, QCheckBox ×4, QLineEdit ×2, QPushButton ×2, QDialog ×1, QVBoxLayout ×1, QSlider ×1, QDialogButtonBox ×1.
- Dimensions / titres directs : setWindowTitle(_tr('Exporter la coupe (PNG)')) L202; setMinimumWidth(460) L203.
- Événements directs (dix premiers maximum) : browse.clicked.connect L230; zoom_slider.valueChanged.connect L319; reset_btn.clicked.connect L326; buttons.accepted.connect L358; buttons.rejected.connect L359.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `section_export_scaled.py:482` — `export_scaled_dialog`

- Nature : fabrique de dialogue.
- Composants repérés : QLabel ×6, QComboBox ×5, QHBoxLayout ×4, QCheckBox ×3, QDialog ×1, QVBoxLayout ×1, QLineEdit ×1, QPushButton ×1, QDialogButtonBox ×1.
- Dimensions / titres directs : setWindowTitle(_tr('Exporter en page (A4 / A3 / échelle)')) L505; setMinimumWidth(500) L506.
- Événements directs (dix premiers maximum) : browse.clicked.connect L593; bb.accepted.connect L598; bb.rejected.connect L599.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `splash.py:36` — `PluginSplash`

- Nature : classe, bases QDialog.
- Composants repérés : QLabel ×5, QVBoxLayout ×1, QProgressBar ×1, QTimer ×1, QPixmap ×1.
- Dimensions / titres directs : setFixedHeight(6) L114; setFixedWidth(400) L132.
- Événements directs (dix premiers maximum) : self._watchdog.timeout.connect L141.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step1_config.py:20` — `Step1Config`

- Nature : classe, bases QWidget.
- Composants repérés : QLabel ×4, QComboBox ×3, QLineEdit ×2, QHBoxLayout ×2, QPushButton ×2, QSettings ×2, QVBoxLayout ×1, QGroupBox ×1, QFormLayout ×1, QWidget ×1, QDoubleSpinBox ×1, QCheckBox ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : self.project_dir_edit.textChanged.connect L61; self.project_dir_btn.clicked.connect L65; self.reopen_check.toggled.connect L128; self.lang_combo.currentIndexChanged.connect L152; open_btn.clicked.connect L160; self.name_edit.textChanged.connect L176; self.project_dir_edit.textChanged.connect L177; self.crs_widget.crsChanged.connect L178; self.units_combo.currentIndexChanged.connect L180.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step2_import.py:156` — `DropZone`

- Nature : classe, bases QFrame.
- Composants repérés : QHBoxLayout ×1, QLabel ×1, QPushButton ×1.
- Dimensions / titres directs : setMinimumWidth(80) L188; setMinimumWidth(78) L203; setFixedHeight(26) L205; setMinimumHeight(40) L170; setMinimumHeight(34) L173.
- Événements directs (dix premiers maximum) : self.btn.clicked.connect L206.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step2_import.py:371` — `ImportTab`

- Nature : classe, bases QWidget.
- Composants repérés : QVBoxLayout ×8, QLabel ×6, QPushButton ×4, QGroupBox ×3, QTableWidget ×2, QHBoxLayout ×2, QRadioButton ×2, QFrame ×2, QTableWidgetItem ×2, QScrollArea ×1, QWidget ×1, QComboBox ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : self.drop_zone.file_dropped.connect L420; self.drop_zone.files_dropped.connect L421; mg.toggled.connect L461; self.editor_btn.clicked.connect L576; self.dip_standard.toggled.connect L475; self.dip_historic.toggled.connect L476; self.structure_button.clicked.connect L505; self.keep_composite_button.clicked.connect L539; self.split_composite_button.clicked.connect L544; combo.currentIndexChanged.connect L1009.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step2_import.py:1485` — `GroupedValidationPanel`

- Nature : classe, bases QWidget.
- Composants repérés : QLabel ×6, QVBoxLayout ×2, QHBoxLayout ×2, QWidget ×2, QComboBox ×1, QScrollArea ×1, QPushButton ×1.
- Dimensions / titres directs : setMinimumHeight(64) L1530; setFixedWidth(14) L1710; setFixedHeight(22) L1734; setMinimumWidth(74) L1735.
- Événements directs (dix premiers maximum) : self.filter_combo.currentIndexChanged.connect L1519; button.clicked.connect L1738.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step2_import.py:1754` — `FamilyChip`

- Nature : classe, bases QPushButton.
- Composants repérés : aucun constructeur Qt direct.
- Dimensions / titres directs : setMinimumHeight(22) L1779.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step2_import.py:1831` — `Step2Import`

- Nature : classe, bases QWidget.
- Composants repérés : QLabel ×8, QVBoxLayout ×5, QPushButton ×4, QHBoxLayout ×3, QWidget ×3, QFrame ×2, QGridLayout ×2, QColor ×2, QTabWidget ×1, QGroupBox ×1, QSplitter ×1.
- Dimensions / titres directs : setMinimumHeight(240) L1990; setMinimumHeight(96) L1991; setFixedHeight(22) L2129; setFixedWidth(14) L2159; setFixedHeight(1) L1928; setFixedHeight(24) L2204; setFixedHeight(22) L2229.
- Événements directs (dix premiers maximum) : self.router_zone.files_dropped.connect L1870; self.tab_widget.currentChanged.connect L1963; clear_btn.clicked.connect L2130; toggle.clicked.connect L1958; chip.clicked.connect L1951; button.clicked.connect L2209; replace_btn.clicked.connect L2231.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step3_geometry.py:67` — `Step3Geometry`

- Nature : classe, bases QWidget.
- Composants repérés : QTableWidgetItem ×6, QLabel ×3, QVBoxLayout ×2, QPushButton ×1, QProgressBar ×1, QGroupBox ×1, QTableWidget ×1.
- Dimensions / titres directs : setMinimumHeight(28) L99; setMinimumHeight(0) L142.
- Événements directs (dix premiers maximum) : self.run_btn.clicked.connect L101; self._task.progressChanged.connect L173; self._task.taskCompleted.connect L174; self._task.taskTerminated.connect L175.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step4_section.py:20` — `SectionMapTool`

- Nature : classe, bases QgsMapTool.
- Composants repérés : QColor ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `step4_section.py:95` — `Step4Section`

- Nature : classe, bases QWidget.
- Composants repérés : QVBoxLayout ×4, QLabel ×4, QPushButton ×4, QGroupBox ×2, QHBoxLayout ×1, QWidget ×1.
- Dimensions / titres directs : setMinimumHeight(28) L125; setMinimumHeight(28) L172.
- Événements directs (dix premiers maximum) : self.draw_btn.clicked.connect L128; self.cancel_draw_btn.clicked.connect L137; self.undo_line_btn.clicked.connect L144; self.gen_btn.clicked.connect L175; self._tool.line_created.connect L215; self._tool.draw_cancelled.connect L216.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `stepper.py:17` — `StepIndicator`

- Nature : classe, bases QWidget.
- Composants repérés : QColor ×9, QPen ×2, QPainter ×1, QFont ×1, QBrush ×1.
- Dimensions / titres directs : setFixedSize(26, 26) L24.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `stepper.py:53` — `StepperWidget`

- Nature : classe, bases QWidget.
- Composants repérés : QHBoxLayout ×1, QVBoxLayout ×1, QLabel ×1, QFrame ×1.
- Dimensions / titres directs : setFixedHeight(46) L60; setFixedHeight(2) L104; setMinimumWidth(20) L105.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `structure_analysis_dialog.py:76` — `_StructureRoseWidget`

- Nature : classe, bases QWidget.
- Composants repérés : QPointF ×10, QColor ×4, QPen ×3, QPainter ×1, QFont ×1, QRectF ×1, QPainterPath ×1, QBrush ×1.
- Dimensions / titres directs : setMinimumSize(260, 260) L86.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `structure_analysis_dialog.py:170` — `_StructureStereonetWidget`

- Nature : classe, bases QWidget.
- Composants repérés : QPointF ×14, QColor ×13, QPen ×8, QBrush ×3, QPixmap ×2, QImage ×2, QRectF ×2, QPainterPath ×2, QPainter ×2, QFont ×1.
- Dimensions / titres directs : setMinimumSize(260, 260) L195.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `structure_analysis_dialog.py:553` — `StructureAnalysisDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QLabel ×8, QComboBox ×4, QVBoxLayout ×3, QHBoxLayout ×1, QGridLayout ×1, QDialogButtonBox ×1, QColor ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Analyse des structures')) L559; resize(940, 640) L561; setMinimumSize(880, 560) L562.
- Événements directs (dix premiers maximum) : self._stereonet_widget.point_clicked.connect L577; self._stereonet_widget.empty_clicked.connect L578; self.scope_combo.currentIndexChanged.connect L585; self.family_combo.currentIndexChanged.connect L597; self.type_combo.currentIndexChanged.connect L602; self.rose_mode.currentIndexChanged.connect L608; buttons.rejected.connect L655.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d.py:33` — `View3DWidget`

- Nature : classe, bases QWidget.
- Composants repérés : QVBoxLayout ×2, QSplitter ×1, QWidget ×1, QLabel ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : self.canvas.hover_changed.connect L79.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d_canvas.py:93` — `View3DCanvas`

- Nature : classe, bases QWidget.
- Composants repérés : QColor ×9, QPushButton ×3, QFrame ×2, QHBoxLayout ×2, QComboBox ×1, QPainter ×1, QTimer ×1, QPen ×1, QFont ×1.
- Dimensions / titres directs : aucune dimension/titre directe détectée.
- Événements directs (dix premiers maximum) : self.combo_cam.currentIndexChanged.connect L281; self.btn_zoom_all.clicked.connect L316; self.btn_center_sel.clicked.connect L321; self.btn_help.clicked.connect L330; timer.timeout.connect L1488.
- Libellés littéraux directs (partiels) : ⛶, 🎯, ❓.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d_dialogs.py:19` — `_AssayElementDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QVBoxLayout ×1, QCheckBox ×1, QListWidget ×1, QLabel ×1, QDialogButtonBox ×1, QListWidgetItem ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Éléments affichés en 3D')) L38; setMinimumWidth(340) L39.
- Événements directs (dix premiers maximum) : buttons.accepted.connect L74; buttons.rejected.connect L75; self.chk_mirror.toggled.connect L78; self.listw.itemChanged.connect L79.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d_imagery_viewer.py:125` — `_ImageryPhotoDialog`

- Nature : classe, bases QDialog.
- Composants repérés : QLabel ×2, QVBoxLayout ×1, QScrollArea ×1, QDialogButtonBox ×1.
- Dimensions / titres directs : setWindowTitle(self.tr('Imagerie — {} · {}–{} m').format(hole_id, f'{from_m:g}', f'{to_m:g}')) L137; setMinimumSize(360, 280) L140.
- Événements directs (dix premiers maximum) : buttons.rejected.connect L163; buttons.accepted.connect L164; self._open_external.clicked.connect L170.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d_v2.py:54` — `_Viewport`

- Nature : classe, bases QWidget.
- Composants repérés : QColor ×2, QPainter ×1, QImage ×1.
- Dimensions / titres directs : setMinimumSize(320, 240) L58.
- Événements directs (dix premiers maximum) : aucune connexion explicite détectée.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `view_3d_v2.py:127` — `View3DV2`

- Nature : classe, bases QWidget.
- Composants repérés : QPushButton ×7, QHBoxLayout ×3, QComboBox ×3, QLabel ×3, QColor ×3, QDoubleSpinBox ×2, QCheckBox ×2, QSettings ×2, QTimer ×1, QVBoxLayout ×1, QWidget ×1, QGridLayout ×1.
- Dimensions / titres directs : setFixedWidth(28) L188; setFixedWidth(28) L189; setMinimumWidth(50) L231.
- Événements directs (dix premiers maximum) : self._timer.timeout.connect L159; self.zone_combo.currentIndexChanged.connect L185; b_prev.clicked.connect L190; b_next.clicked.connect L191; self.exag.valueChanged.connect L210; btn_fit.clicked.connect L213; btn_ref.clicked.connect L218; self.btn_set.toggled.connect L222; b_reset.clicked.connect L284; self.s_gap.valueChanged.connect L301.
- Libellés littéraux directs (partiels) : ◀, ▶.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

### `visualization_dock.py:36` — `VisualizationDock`

- Nature : classe, bases QgsDockWidget.
- Composants repérés : QLabel ×8, QWidget ×2, QVBoxLayout ×2, QFrame ×1, QHBoxLayout ×1, QTabWidget ×1, QPushButton ×1, QSettings ×1.
- Dimensions / titres directs : setMinimumHeight(260) L210; setWindowTitle(_QCA.translate('VisualizationDock', 'DrillMaster — Visualisation')) L319.
- Événements directs (dix premiers maximum) : self.visibilityChanged.connect L64; self.tabs.currentChanged.connect L143; btn.clicked.connect L181.
- Libellés littéraux directs (partiels) : aucun détecté ; textes traduits ou construits non résolus.
- Diagnostic : couverture visuelle et parcours non observés ; vérifier ouverture, mise en page, échelles, états et focus ; aucune anomalie visuelle déduite de ce seul relevé.

## Dialogues et menus créés dynamiquement — inventaire syntaxique

Liste des appels textuels à des classes Qt/QGIS courantes : inclut les appels statiques ; les alias, enveloppes maison, callbacks et contrôles conditionnels peuvent échapper au relevé. Ne démontre pas que la fenêtre est accessible ou utilisée.

- `ui/csv_editor.py` : `QFileDialog QFileDialog.getSaveFileName L531`; `QMessageBox QMessageBox.question L559`; `QMessageBox QMessageBox.warning L521`; `QMessageBox QMessageBox.critical L497`.
- `ui/lithology_structure_dialog.py` : `QMessageBox QMessageBox.information L221`; `QMessageBox QMessageBox.warning L352`; `QMessageBox QMessageBox.warning L332`; `QMessageBox QMessageBox.warning L337`; `QMessageBox QMessageBox.warning L342`; `QMessageBox QMessageBox.warning L360`.
- `ui/main_dock.py` : `QMenu QMenu L181`; `QDialog QDialog L674`; `QMessageBox QMessageBox L706`; `QMessageBox QMessageBox.warning L475`; `QMessageBox QMessageBox.critical L730`; `QMessageBox QMessageBox.critical L491`.
- `ui/reference_dialog.py` : `QMessageBox QMessageBox.question L899`; `QMessageBox QMessageBox.question L954`; `QMessageBox QMessageBox.question L1018`; `QColorDialog QColorDialog L803`; `QMessageBox QMessageBox.information L892`; `QMessageBox QMessageBox.information L926`; `QMessageBox QMessageBox.information L937`; `QMessageBox QMessageBox.information L978`; `QMessageBox QMessageBox.information L998`; `QMessageBox QMessageBox.question L1125`; `QMessageBox QMessageBox.warning L1096`.
- `ui/section_dock.py` : `QColorDialog QColorDialog.getColor L7859`; `QMenu QMenu L11075`.
- `ui/section_export.py` : `QDialog QDialog L201`; `QMessageBox QMessageBox.warning L55`; `QMessageBox QMessageBox.information L59`; `QFileDialog QFileDialog.getSaveFileName L221`; `QMessageBox QMessageBox.information L154`; `QMessageBox QMessageBox.warning L158`.
- `ui/section_export_scaled.py` : `QDialog QDialog L504`; `QMessageBox QMessageBox.information if ok else QMessageBox.warning L620`; `QMessageBox QMessageBox.information L485`; `QFileDialog QFileDialog.getSaveFileName L585`.
- `ui/section_holes.py` : `QMenu QMenu L118`.
- `ui/step1_config.py` : `QFileDialog QFileDialog.getExistingDirectory L298`; `QFileDialog QFileDialog.getExistingDirectory L305`; `QMessageBox QMessageBox.warning L311`.
- `ui/step2_import.py` : `QFileDialog QFileDialog.getOpenFileName L217`; `QFileDialog QFileDialog.getOpenFileNames L211`.
- `ui/step4_section.py` : `QInputDialog QInputDialog.getDouble L299`.
- `ui/view_3d_canvas.py` : `QMessageBox QMessageBox.information L344`.
