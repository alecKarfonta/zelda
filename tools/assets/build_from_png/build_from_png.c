#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <libgen.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include "../n64texconv/src/libn64texconv/bin2c.h"
#include "../n64texconv/src/libn64texconv/n64texconv.h"

#define NUM_FORMATS 9
static const struct fmt_info {
    const char* name;
    int fmt;
    int siz;
} fmt_map[NUM_FORMATS] = {
    // clang-format off
    { "i4",     G_IM_FMT_I,    G_IM_SIZ_4b,  },
    { "i8",     G_IM_FMT_I,    G_IM_SIZ_8b,  },
    { "ci4",    G_IM_FMT_CI,   G_IM_SIZ_4b,  },
    { "ci8",    G_IM_FMT_CI,   G_IM_SIZ_8b,  },
    { "ia4",    G_IM_FMT_IA,   G_IM_SIZ_4b,  },
    { "ia8",    G_IM_FMT_IA,   G_IM_SIZ_8b,  },
    { "ia16",   G_IM_FMT_IA,   G_IM_SIZ_16b, },
    { "rgba16", G_IM_FMT_RGBA, G_IM_SIZ_16b, },
    { "rgba32", G_IM_FMT_RGBA, G_IM_SIZ_32b, },
    // clang-format on
};

enum sub_format {
    SUBFMT_SPLIT_LO,
    SUBFMT_SPLIT_HI,
    SUBFMT_MAX,
    SUBFMT_NONE
};
static const char* subfmt_map[SUBFMT_MAX] = {
    [SUBFMT_SPLIT_LO] = "split_lo",
    [SUBFMT_SPLIT_HI] = "split_hi",
};

#define strequ(s1, s2) (strcmp(s1, s2) == 0)
#define strstartswith(s, prefix) (strncmp(s, prefix, strlen(prefix)) == 0)

static bool strendswith(const char* s, const char* suffix) {
    size_t len_s = strlen(s);
    size_t len_suffix = strlen(suffix);
    return (len_s >= len_suffix) && (strncmp(s + len_s - len_suffix, suffix, len_suffix) == 0);
}

// Function to check if file exists
static bool file_exists(const char* path) {
    struct stat st;
    return stat(path, &st) == 0;
}

// Function to slice large HD textures into 64×32 chunks in a subdirectory
static bool slice_hd_texture(const char* input_path, const char* output_dir, const char* unused_base_name) {
    // Extract base name (with format) from input_path, stripping .png and .ss/.hd
    char* input_path_copy = strdup(input_path);
    char* file = basename(input_path_copy);
    char base_name[256];
    strncpy(base_name, file, sizeof(base_name) - 1);
    base_name[sizeof(base_name) - 1] = '\0';
    // Remove .ss or .hd extension if present
    char* ext = strrchr(base_name, '.');
    if (ext && (strcmp(ext, ".ss") == 0 || strcmp(ext, ".hd") == 0)) {
        *ext = '\0';
    }
    // Remove .png extension if present
    ext = strrchr(base_name, '.');
    if (ext && strcmp(ext, ".png") == 0) {
        *ext = '\0';
    }
    // Use only the part before the first dot for the slice directory
    char* first_dot = strchr(base_name, '.');
    char slice_dir_base[256];
    if (first_dot) {
        size_t len = first_dot - base_name;
        strncpy(slice_dir_base, base_name, len);
        slice_dir_base[len] = '\0';
    } else {
        strncpy(slice_dir_base, base_name, sizeof(slice_dir_base) - 1);
        slice_dir_base[sizeof(slice_dir_base) - 1] = '\0';
    }
    char slice_dir[1024];
    snprintf(slice_dir, sizeof(slice_dir), "%s/%s_slices", output_dir, slice_dir_base);
    char cmd[1024];
    int result;
    // Create output subdirectory if it doesn't exist
    snprintf(cmd, sizeof(cmd), "mkdir -p %s", slice_dir);
    system(cmd);
    // Get image dimensions
    snprintf(cmd, sizeof(cmd), "identify -format '%%w %%h' %s", input_path);
    FILE* pipe = popen(cmd, "r");
    if (!pipe) { free(input_path_copy); return false; }
    int width, height;
    if (fscanf(pipe, "%d %d", &width, &height) != 2) {
        pclose(pipe);
        free(input_path_copy);
        return false;
    }
    pclose(pipe);
    printf("Slicing HD texture: %dx%d\n", width, height);
    int slice_width = 64;
    int slice_height = 32;
    int slices_x = (width + slice_width - 1) / slice_width;
    int slices_y = (height + slice_height - 1) / slice_height;
    printf("Creating %dx%d slices (%d total) in %s\n", slices_x, slices_y, slices_x * slices_y, slice_dir);
    for (int y = 0; y < slices_y; y++) {
        for (int x = 0; x < slices_x; x++) {
            char slice_name[256];
            snprintf(slice_name, sizeof(slice_name), "%s_slice_%d_%d.png", base_name, y, x);
            snprintf(cmd, sizeof(cmd),
                "convert %s -crop %dx%d+%d+%d %s/%s",
                input_path,
                slice_width, slice_height,
                x * slice_width, y * slice_height,
                slice_dir, slice_name);
            result = system(cmd);
            if (result != 0) {
                printf("Error creating slice %s\n", slice_name);
                free(input_path_copy);
                return false;
            }
        }
    }
    free(input_path_copy);
    return true;
}

// Function to check for HD texture variants (.ss or .hd)
static char* check_for_hd_texture(const char* standard_png_path) {
    static const char* exts[] = { ".ss", ".hd" };
    for (size_t i = 0; i < sizeof(exts)/sizeof(*exts); ++i) {
        char* hd_path = malloc(strlen(standard_png_path) + strlen(exts[i]) + 1);
        strcpy(hd_path, standard_png_path);
        strcat(hd_path, exts[i]);
        if (file_exists(hd_path)) {
            return hd_path;
        }
        free(hd_path);
    }
    return NULL;
}

// Refactored PNG processing logic
static int process_png(const char* png_p, const char* out_dir_p, char** in_dirs, int num_in_dirs) {
    const struct fmt_info* fmt;
    enum sub_format subfmt;
    int elem_size;
    size_t len_png_p_prefix;
    char* tlut_name = NULL;
    int tlut_elem_size = -1;

    {
        char* png_p_buf = strdup(png_p);
        bool success =
            parse_png_p(png_p_buf, &fmt, &subfmt, &elem_size, &len_png_p_prefix, &tlut_name, &tlut_elem_size, true);
        free(png_p_buf);
        if (!success) {
            fprintf(stderr, "Failed to parse PNG path: %s\n", png_p);
            return EXIT_FAILURE;
        }
    }

    bool success;

    if (fmt->fmt != G_IM_FMT_CI) {
        success = handle_non_ci(png_p, fmt, elem_size, out_dir_p);
    } else {
        if (tlut_name == NULL) {
            success = handle_ci_single(png_p, fmt, subfmt, elem_size, out_dir_p, len_png_p_prefix);
        } else {
            success =
                handle_ci_shared_tlut(png_p, fmt, subfmt, out_dir_p, in_dirs, num_in_dirs, tlut_name, tlut_elem_size);
            free(tlut_name);
        }
    }

    return success ? EXIT_SUCCESS : EXIT_FAILURE;
}

int main(int argc, char** argv) {
    if (argc < 3) {
    usage:
        fprintf(stderr,
                "Usage: build_from_png path/to/file.png path/to/out/folder/ [path/to/input/folder1/ ...]\n"
                "The png file should be named like:\n"
                " - texName.format[.<u32|u64>].png (non-ci formats or ci formats with a non-shared tlut)\n"
                " - texName.ci<4|8>.tlut_tlutName[_<u32|u64>][.<u32|u64>].png (ci formats with a shared tlut)\n");
        return EXIT_FAILURE;
    }
    const char* png_p = argv[1];
    const char* out_dir_p = argv[2];
    char** in_dirs = argv + 3;
    const int num_in_dirs = argc - 3;

    // Only process standard PNGs (slices or originals)
    return process_png(png_p, out_dir_p, in_dirs, num_in_dirs);
}
