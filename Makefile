# Slicing HD textures (.ss or .hd) into 64x32 chunks before main PNG build
# This will create slices in the appropriate directory for each .ss/.hd file

# Nintendo logo texture is 256x128 in original, 768x128 in HD (3x scale)
extracted/$(VERSION)/assets/textures/nintendo_rogo_static_slices/%.png: extracted/$(VERSION)/assets/textures/nintendo_rogo_static/%.ss | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< --original-width=256 --original-height=128 --scale=3 --target-width=64 --target-height=32

extracted/$(VERSION)/assets/textures/nintendo_rogo_static_slices/%.png: extracted/$(VERSION)/assets/textures/nintendo_rogo_static/%.hd | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< --original-width=256 --original-height=128 --scale=3 --target-width=64 --target-height=32

assets/textures/nintendo_rogo_static_slices/%.png: assets/textures/nintendo_rogo_static/%.ss | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< --original-width=256 --original-height=128 --scale=3 --target-width=64 --target-height=32

assets/textures/nintendo_rogo_static_slices/%.png: assets/textures/nintendo_rogo_static/%.hd | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< --original-width=256 --original-height=128 --scale=3 --target-width=64 --target-height=32

# Generic rules for other HD textures - uses default parameters
extracted/$(VERSION)/assets/%_slices/%.png: extracted/$(VERSION)/assets/%.ss | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< $(dir $@)

extracted/$(VERSION)/assets/%_slices/%.png: extracted/$(VERSION)/assets/%.hd | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< $(dir $@)

assets/%_slices/%.png: assets/%.ss | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< $(dir $@)

assets/%_slices/%.png: assets/%.hd | tools/assets/build_from_png/slice_hd_texture
	tools/assets/build_from_png/slice_hd_texture $< $(dir $@)

# Ensure the slicer tool is built
TOOLS_BUILD := tools/assets/build_from_png/slice_hd_texture 