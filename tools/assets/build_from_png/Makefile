CC ?= gcc
# Suppress format-truncation and other warnings that may trigger -Werror in some environments
CFLAGS := -O2 -Wall -Wno-error -Wno-format-truncation -Wno-format-overflow

all: slice_hd_texture

slice_hd_texture: slice_hd_texture.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f slice_hd_texture 