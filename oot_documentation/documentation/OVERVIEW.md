# Repository Overview: Z64 Romhacking Tutorials

## Purpose and Goals

This repository serves as a comprehensive educational resource for understanding and modifying Zelda64 games, specifically **The Legend of Zelda: Ocarina of Time** and **Majora's Mask** for the Nintendo 64. The project aims to bridge the gap between curiosity and capability in the romhacking community by providing structured learning materials for all skill levels.

### Primary Objectives

1. **Democratize Knowledge**: Make advanced romhacking techniques accessible to newcomers while providing depth for experienced modders
2. **Preserve Expertise**: Document the collective knowledge of the Z64 romhacking community in a structured, searchable format
3. **Enable Creation**: Provide practical, hands-on tutorials that lead to actual mod development
4. **Foster Understanding**: Explain not just the "how" but the "why" behind game modification techniques

## Target Audience

### Beginners
- **Game enthusiasts** curious about how their favorite games work internally
- **Aspiring modders** with basic computer literacy but no prior romhacking experience
- **Students** learning game development concepts through reverse engineering

### Intermediate Users
- **Hobby modders** looking to expand their toolkit and understanding
- **Developers** interested in N64 architecture and game engine design
- **Researchers** studying retro game development techniques

### Advanced Users
- **Experienced romhackers** seeking comprehensive reference materials
- **Tool developers** building utilities for the Z64 modding community
- **Academic researchers** studying game preservation and modification

## Content Organization

### 1. Practical Tutorials
**Location**: `custom actors/`, `oot64 overview/`

Step-by-step guides that teach specific modding skills:
- **Custom Actor Development**: Complete workflow from 3D modeling to in-game implementation
- **Game Engine Understanding**: Deep dives into OoT64's internal systems
- **Tool Usage**: Practical guides for essential modding utilities

### 2. Technical Reference
**Location**: `debugging/`, `resources.md`

Comprehensive documentation of:
- **Debugging Techniques**: Console logging, GDB usage, screen printing
- **Tool Ecosystem**: Curated list of essential modding tools and utilities
- **Community Resources**: Links to forums, Discord servers, and expert knowledge

### 3. Applied Examples
**Location**: `examples.md`, `generated/`

Real-world implementations showcasing:
- **Completed Mods**: Functioning examples with source code
- **Advanced Techniques**: Complex interactions, AI behaviors, graphics effects
- **Best Practices**: Proven approaches to common modding challenges

### 4. Development Resources
**Location**: `oot/`

Actual game code and assets including:
- **Decompiled Source**: Working with the OoT decomp project
- **Binary Assets**: Tools and workflows for asset modification
- **Build Systems**: Docker-based development environment

## Learning Pathways

### Path 1: Complete Beginner → Custom Actor Creator
1. **Start**: Basic computer literacy, interest in OoT
2. **Prerequisites**: Learn basic 3D modeling (Blender recommended)
3. **Tutorial**: Follow `custom actors/` step-by-step
4. **Outcome**: Create and inject custom actors into OoT

### Path 2: Programmer → Game Engine Expert
1. **Start**: Programming experience (C preferred)
2. **Deep Dive**: Study `oot64 overview/` technical documentation
3. **Practice**: Explore `debugging/` tools and techniques
4. **Outcome**: Understand OoT64's architecture and systems

### Path 3: Modder → Advanced Developer
1. **Start**: Basic romhacking experience
2. **Expand**: Use `resources.md` to discover advanced tools
3. **Reference**: Utilize `generated/` examples for complex features
4. **Outcome**: Create sophisticated gameplay modifications

## Technical Approaches

### Decomp-Based Modding
- **Advantages**: Full source code access, powerful debugging, maintainable code
- **Tools**: OoT decomp project, modern C compilers, standard debugging tools
- **Use Cases**: Complex gameplay changes, new systems, academic research

### Traditional Romhacking
- **Advantages**: Direct ROM manipulation, established toolchain, immediate results
- **Tools**: SharpOcarina, CustomActorsToolkit, hex editors
- **Use Cases**: Asset replacement, simple modifications, rapid prototyping

## Community Integration

### Documentation Standards
- **Markdown Format**: GitHub-flavored markdown for consistency
- **ISO 8601 Dating**: Standardized timestamps for version tracking
- **CC0 License**: Public domain dedication for maximum accessibility

### Contribution Guidelines
- **Open Source**: All content freely available and modifiable
- **Collaborative**: Community contributions welcomed and encouraged
- **Quality Focus**: Emphasis on clear explanations and working examples

## Success Metrics

This repository succeeds when:
- **Beginners** can follow tutorials and create their first mods
- **Intermediate users** find comprehensive reference materials
- **Advanced users** contribute back to the knowledge base
- **The community** grows and becomes more self-sustaining

## Future Directions

### Planned Expansions
- **Majora's Mask Content**: Extending tutorials to cover MM-specific techniques
- **Advanced Graphics**: Detailed coverage of N64 graphics programming
- **Audio Systems**: Comprehensive guide to music and sound effect modification
- **Multiplayer Concepts**: Exploring network play modifications

### Community Goals
- **Tool Development**: Supporting creation of better modding utilities
- **Knowledge Preservation**: Ensuring expertise isn't lost as community members move on
- **Educational Outreach**: Connecting with academic institutions studying game preservation

## Getting Started

### For Newcomers
1. Read this overview document
2. Check system requirements in relevant tutorial folders
3. Start with `custom actors/part00_setup/`
4. Join community Discord servers listed in `resources.md`

### For Contributors
1. Review existing content for gaps
2. Follow documentation standards
3. Test all code examples before submitting
4. Engage with community feedback

This repository represents the collective effort of the Z64 romhacking community to preserve, organize, and share knowledge. Whether you're here to learn, teach, or simply explore, you're contributing to the ongoing legacy of these beloved games. 