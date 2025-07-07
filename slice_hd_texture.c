// HD Texture Slicer Tool
// This tool slices HD textures into smaller chunks for the game to use.
// 
// Usage: slice_hd_texture <input_file> [options]
//   --target-width=N    Target slice width (default: 64)
//   --target-height=N   Target slice height (default: 32) 
//   --original-width=N  Original texture width for validation
//   --original-height=N Original texture height for validation
//   --scale=N          Expected scale factor (default: 3)
//
// The tool validates that:
// 1. HD texture dimensions are multiples of the original dimensions
// 2. HD texture dimensions match the expected scale factor
// 3. HD texture dimensions are multiples of the target slice dimensions
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <getopt.h>

#define MAX_PATH 4096
#define MAX_CMD 8192

struct Options {
    int target_width;
    int target_height;
    int original_width;
    int original_height;
    int scale;
    const char* input_file;
};

/* Replace '.' or '-' with '_' in-place so the string is a valid C identifier */
static void sanitize_id(char* buf) {
    for (char* p = buf; *p; ++p) {
        if (*p == '.' || *p == '-') *p = '_';
    }
}

static void print_usage(const char* program) {
    fprintf(stderr, "Usage: %s <input_file> [options]\n", program);
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "  --target-width=N     Target slice width (default: 64)\n");
    fprintf(stderr, "  --target-height=N    Target slice height (default: 32)\n");
    fprintf(stderr, "  --original-width=N   Original texture width for validation\n");
    fprintf(stderr, "  --original-height=N  Original texture height for validation\n");
    fprintf(stderr, "  --scale=N           Expected scale factor (default: 3)\n");
    fprintf(stderr, "\nExample: %s nintendo_logo.ss --original-width=256 --original-height=128 --scale=3\n", program);
}

static struct Options parse_options(int argc, char* argv[]) {
    struct Options opts = {
        .target_width = 64,
        .target_height = 32,
        .original_width = 0,
        .original_height = 0,
        .scale = 3,
        .input_file = NULL
    };

    static struct option long_options[] = {
        {"target-width", required_argument, 0, 'w'},
        {"target-height", required_argument, 0, 'h'},
        {"original-width", required_argument, 0, 'x'},
        {"original-height", required_argument, 0, 'y'},
        {"scale", required_argument, 0, 's'},
        {0, 0, 0, 0}
    };

    int option_index = 0;
    int c;

    while ((c = getopt_long(argc, argv, "w:h:x:y:s:", long_options, &option_index)) != -1) {
        switch (c) {
            case 'w': opts.target_width = atoi(optarg); break;
            case 'h': opts.target_height = atoi(optarg); break;
            case 'x': opts.original_width = atoi(optarg); break;
            case 'y': opts.original_height = atoi(optarg); break;
            case 's': opts.scale = atoi(optarg); break;
            default: print_usage(argv[0]); exit(1);
        }
    }

    if (optind >= argc) {
        fprintf(stderr, "Error: Input file required\n");
        print_usage(argv[0]);
        exit(1);
    }

    opts.input_file = argv[optind];
    return opts;
}

static int validate_dimensions(int width, int height, const struct Options* opts) {
    // If original dimensions provided, validate scale factor
    if (opts->original_width > 0 && opts->original_height > 0) {
        if (width != opts->original_width * opts->scale || 
            height != opts->original_height * opts->scale) {
            fprintf(stderr, "Error: HD texture dimensions (%dx%d) don't match expected scaled dimensions (%dx%d)\n",
                    width, height,
                    opts->original_width * opts->scale,
                    opts->original_height * opts->scale);
            return 0;
        }
    }

    // Validate dimensions are multiples of slice size
    if (width % opts->target_width != 0 || height % opts->target_height != 0) {
        fprintf(stderr, "Error: HD texture dimensions (%dx%d) must be multiples of slice dimensions (%dx%d)\n",
                width, height, opts->target_width, opts->target_height);
        return 0;
    }

    return 1;
}

int main(int argc, char* argv[]) {
    struct Options opts = parse_options(argc, argv);
    
    char base_name[MAX_PATH];
    char format_suffix[MAX_PATH];
    char output_dir[MAX_PATH];
    char cmd[MAX_CMD];
    
    // Extract base name and format suffix
    char *dot = strrchr(opts.input_file, '.');
    if (!dot) {
        fprintf(stderr, "Error: Input file must have a format extension (e.g., .ss, .hd)\n");
        return 1;
    }
    
    // Split into base name and format
    size_t base_len = dot - opts.input_file;
    if (base_len >= MAX_PATH) {
        fprintf(stderr, "Error: Base name too long\n");
        return 1;
    }
    strncpy(base_name, opts.input_file, base_len);
    base_name[base_len] = '\0';
    strncpy(format_suffix, dot, MAX_PATH - 1);
    format_suffix[MAX_PATH - 1] = '\0';
    
    /* Extract just the file component of the texture path */
    char *filename = strrchr(base_name, '/');
    if (filename) {
        filename++; /* skip '/' */
    } else {
        filename = base_name;
    }

    /* If the filename contains the common pattern "_Tex_" (e.g. the standard
     * naming convention produced by the OoT asset extractor), drop that suffix
     * and everything that follows so that the generated identifiers are more
     * concise and predictable (matching what the game code tends to use, such
     * as `nintendo_rogo_static_hd_slices`).
     */
    char trimmed_name[MAX_PATH];
    strncpy(trimmed_name, filename, MAX_PATH - 1);
    trimmed_name[MAX_PATH - 1] = '\0';

    char *tex_marker = strstr(trimmed_name, "_Tex_");
    if (tex_marker) {
        *tex_marker = '\0';
    }

    /* Additionally strip any trailing format suffix (e.g. .i4, .i8, .rgba16)
     * that may still be present after the previous truncation.  Find the last
     * dot and terminate the string there.
     */
    char *last_dot = strrchr(trimmed_name, '.');
    if (last_dot) {
        *last_dot = '\0';
    }

    char header_base_name[MAX_PATH];
    strncpy(header_base_name, trimmed_name, MAX_PATH - 1);
    header_base_name[MAX_PATH - 1] = '\0';
    sanitize_id(header_base_name);
    
    // Create output directory path
    char *last_slash = strrchr(opts.input_file, '/');
    if (last_slash) {
        size_t dir_len = last_slash - opts.input_file;
        if (dir_len >= MAX_PATH) {
            fprintf(stderr, "Error: Directory path too long\n");
            return 1;
        }
        strncpy(output_dir, opts.input_file, dir_len);
        output_dir[dir_len] = '\0';
    } else {
        strcpy(output_dir, ".");
    }
    
    // Create slices directory
    char slices_dir[MAX_PATH];
    if (snprintf(slices_dir, MAX_PATH, "%s/%s_slices", output_dir, base_name) >= MAX_PATH) {
        fprintf(stderr, "Error: Slice directory path too long\n");
        return 1;
    }
    
    // Create output directory
    snprintf(cmd, MAX_CMD, "mkdir -p %s", slices_dir);
    system(cmd);
    
    // Get image dimensions first
    snprintf(cmd, MAX_CMD, "identify -format '%%w %%h' '%s'", opts.input_file);
    FILE *pipe = popen(cmd, "r");
    if (!pipe) {
        fprintf(stderr, "Error: Failed to get image dimensions\n");
        return 1;
    }
    
    int width, height;
    if (fscanf(pipe, "%d %d", &width, &height) != 2) {
        pclose(pipe);
        fprintf(stderr, "Error: Failed to parse image dimensions\n");
        return 1;
    }
    pclose(pipe);

    // Validate dimensions
    if (!validate_dimensions(width, height, &opts)) {
        return 1;
    }
    
    printf("Slicing HD texture: %dx%d\n", width, height);
    
    // Calculate slice dimensions and count
    int slices_x = width / opts.target_width;
    int slices_y = height / opts.target_height;
    
    printf("Creating %dx%d slices (%d total) in %s\n", slices_x, slices_y, slices_x * slices_y, slices_dir);
    
    // Create slices using ImageMagick
    for (int y = 0; y < slices_y; y++) {
        for (int x = 0; x < slices_x; x++) {
            char slice_name[MAX_PATH];
            if (snprintf(slice_name, MAX_PATH, "slice_%d_%d.i8.png", y, x) >= MAX_PATH) {
                fprintf(stderr, "Error: Slice name too long\n");
                return 1;
            }
            
            if (snprintf(cmd, MAX_CMD,
                "convert '%s' -crop %dx%d+%d+%d '%s/%s'",
                opts.input_file,
                opts.target_width, opts.target_height,
                x * opts.target_width, y * opts.target_height,
                slices_dir, slice_name) >= MAX_CMD) {
                fprintf(stderr, "Error: Command too long\n");
                return 1;
            }
            
            printf("Creating slice %s\n", slice_name);
            int result = system(cmd);
            if (result != 0) {
                fprintf(stderr, "Error: Failed to create slice %s\n", slice_name);
                return 1;
            }
        }
    }
    
    // Generate header file with slice array
    char header_file[MAX_PATH];
    if (snprintf(header_file, MAX_PATH, "%s/%s_hd_slices.h", slices_dir, header_base_name) >= MAX_PATH) {
        fprintf(stderr, "Error: Header file path too long\n");
        return 1;
    }
    
    FILE *header = fopen(header_file, "w");
    if (!header) {
        fprintf(stderr, "Error: Failed to create header file %s\n", header_file);
        return 1;
    }
    
    // Write header file
    fprintf(header, "// Auto-generated HD texture slice array\n");
    fprintf(header, "// Generated from: %s\n", opts.input_file);
    fprintf(header, "// Original dimensions: %dx%d\n", opts.original_width, opts.original_height);
    fprintf(header, "// HD dimensions: %dx%d (scale: %dx)\n", width, height, opts.scale);
    fprintf(header, "// Slice dimensions: %dx%d\n\n", opts.target_width, opts.target_height);
    fprintf(header, "#ifndef %s_HD_SLICES_H\n", header_base_name);
    fprintf(header, "#define %s_HD_SLICES_H\n\n", header_base_name);
    
    // Declare extern for each slice
    for (int y = 0; y < slices_y; y++) {
        for (int x = 0; x < slices_x; x++) {
            fprintf(header, "extern u8 %s_slice_%d_%d[];\n", header_base_name, y, x);
        }
    }
    
    fprintf(header, "\n// Slice array for easy access\n");
    fprintf(header, "extern u8* %s_hd_slices[%d][%d];\n\n", header_base_name, slices_y, slices_x);
    fprintf(header, "#endif // %s_HD_SLICES_H\n", header_base_name);
    fclose(header);
    
    // Generate C file with slice array initialization
    char c_file[MAX_PATH];
    if (snprintf(c_file, MAX_PATH, "%s/%s_hd_slices.c", slices_dir, header_base_name) >= MAX_PATH) {
        fprintf(stderr, "Error: C file path too long\n");
        return 1;
    }
    
    FILE *cfile = fopen(c_file, "w");
    if (!cfile) {
        fprintf(stderr, "Error: Failed to create C file %s\n", c_file);
        return 1;
    }
    
    // Write C file
    fprintf(cfile, "// Auto-generated HD texture slice array implementation\n");
    fprintf(cfile, "// Generated from: %s\n\n", opts.input_file);
    fprintf(cfile, "#include \"%s_hd_slices.h\"\n\n", header_base_name);
    
    // Declare each slice
    for (int y = 0; y < slices_y; y++) {
        for (int x = 0; x < slices_x; x++) {
            fprintf(cfile, "extern u8 %s_slice_%d_%d[];\n", header_base_name, y, x);
        }
    }
    
    fprintf(cfile, "\n// Slice array initialization\n");
    fprintf(cfile, "u8* %s_hd_slices[%d][%d] = {\n", header_base_name, slices_y, slices_x);
    
    for (int y = 0; y < slices_y; y++) {
        fprintf(cfile, "    {");
        for (int x = 0; x < slices_x; x++) {
            fprintf(cfile, " %s_slice_%d_%d", header_base_name, y, x);
            if (x < slices_x - 1) fprintf(cfile, ",");
        }
        fprintf(cfile, " }");
        if (y < slices_y - 1) fprintf(cfile, ",");
        fprintf(cfile, "\n");
    }
    
    fprintf(cfile, "};\n");
    fclose(cfile);
    
    printf("Generated header file: %s\n", header_file);
    printf("Generated C file: %s\n", c_file);
    printf("HD texture slicing completed successfully!\n");
    
    return 0;
} 