import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.files import get, apply_conandata_patches, copy, export_conandata_patches, rmdir

required_conan_version = ">=2.0.6"

# @TODO: skip tests if private headers aren't installed,
# because current link test requires private headers


class FontForgeConan(ConanFile):
    name = "fontforge"
    package_type = "library"

    license = ("GPLv3-or-later", "revised-BSD")
    homepage = "https://fontforge.org"
    description = ("FontForge is a free (libre) font editor for Windows, Mac OS X and GNU+Linux. Use it to create, "
                   "edit and convert fonts in OpenType, TrueType, UFO, CID-keyed, Multiple Master, and many other "
                   "formats.")
    topics = "fonts"

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "install_private_headers": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "install_private_headers": True,
    }

    def requirements(self):
        # @TODO: Freetype's requires aren't sorted properly
        # /usr/bin/ld: /home/user/.conan2/p/b/freet1d6ed4030d063/p/lib/libfreetype.a(src_sfnt_sfnt.c.o): in function `sfnt_init_face':
        # sfnt.c:(.text+0x1389a): undefined reference to `BrotliDecoderDecompress'
        # /usr/bin/ld: /home/user/.conan2/p/b/freet1d6ed4030d063/p/lib/libfreetype.a(src_bzip2_ftbzip2.c.o): in function `ft_bzip2_stream_close':
        # ftbzip2.c:(.text+0x49): undefined reference to `BZ2_bzDecompressEnd'
        # /usr/bin/ld: /home/user/.conan2/p/b/freet1d6ed4030d063/p/lib/libfreetype.a(src_bzip2_ftbzip2.c.o): in function `ft_bzip2_file_fill_output':
        # ftbzip2.c:(.text+0xf7): undefined reference to `BZ2_bzDecompress'
        # /usr/bin/ld: /home/user/.conan2/p/b/freet1d6ed4030d063/p/lib/libfreetype.a(src_bzip2_ftbzip2.c.o): in function `ft_bzip2_stream_io':
        # ftbzip2.c:(.text+0x2ff): undefined reference to `BZ2_bzDecompressEnd'
        # /usr/bin/ld: ftbzip2.c:(.text+0x355): undefined reference to `BZ2_bzDecompressInit'
        # /usr/bin/ld: /home/user/.conan2/p/b/freet1d6ed4030d063/p/lib/libfreetype.a(src_bzip2_ftbzip2.c.o): in function `FT_Stream_OpenBzip2':
        # ftbzip2.c:(.text+0x5d4): undefined reference to `BZ2_bzDecompressInit'
        #
        # with open(os.path.join(self.source_folder, "fontforge/CMakeLists.txt"), "a") as CMakeLists:
        #     CMakeLists.writelines([
        #         "find_package(brotli REQUIRED)\n",
        #         "find_package(BZip2 REQUIRED)\n",
        #         "target_link_libraries(fontforge PUBLIC brotli::brotli BZip2::BZip2)"
        #     ])
        self.requires("freetype/2.13.2")

        self.requires("libxml2/2.12.7")
        self.requires("giflib/5.2.2")
        self.requires("libjpeg/9f")
        self.requires("libpng/1.6.43")

        # self.requires("libtiff/4.6.0")
        # jbig and libdeflate are required by libtiff
        # Conan auto finds them, but linker doesn't, unless they're added here manually
        # self.requires("jbig/20160605")
        # self.requires("libdeflate/1.20")

        self.requires("glib/2.78.3")

    def build_requirements(self):
        self.tool_requires("gettext/0.22.5")

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.variables["ENABLE_GUI"] = "OFF"
        tc.variables["ENABLE_PYTHON_SCRIPTING"] = "OFF"
        tc.variables["ENABLE_PYTHON_EXTENSION"] = "OFF"
        tc.variables["ENABLE_LIBSPIRO"] = "OFF"
        tc.variables["INSTALL_PRIVATE_HEADERS"] = self.options.install_private_headers
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

        # patch_folder = os.path.join(self.export_sources_folder, "patches/" + self.version)
        # if self.version == "20230101":
        #     patch(self, patch_file=os.path.join(patch_folder, "pie.patch"))
        # patch(self, patch_file=os.path.join(patch_folder, "FindGLib.patch"))

        # android-ndk-r20/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/pwd.h
        # #if __ANDROID_API__ >= 26
        # struct passwd* getpwent(void) __INTRODUCED_IN(26);
        # void setpwent(void) __INTRODUCED_IN(26);
        # void endpwent(void) __INTRODUCED_IN(26);
        # #endif /* __ANDROID_API__ >= 26 */
        # patch(self, patch_file=os.path.join(patch_folder, "gutils-fsys.patch"))

        # patch(self, patch_file=os.path.join(patch_folder, "InstallLibrary.patch"))

        # @TODO: openlibm
        # patch(self, patch_file=os.path.join(patch_folder, "splinestroke-complex-math.patch"))
        # projectDir.resolve("patches/$portVersion/FindMathLib.cmake").copyTo(
        #     target = srcDir.resolve("cmake/packages/FindMathLib.cmake"),
        #     overwrite = true
        # )

        # if (minSupportedSdk < 21) {
        #     // fontforge uses newlocale and localeconv, which are not available on Android pre 21 (Lollipop)
        #     // locale_t is available, we should not redefine it while using the BAD_LOCALE_HACK in splinefont.h
        #     //
        #     // From /usr/include/locale.h:
        #     // #if __ANDROID_API__ >= 21
        #     // locale_t duplocale(locale_t __l) __INTRODUCED_IN(21);
        #     // void freelocale(locale_t __l) __INTRODUCED_IN(21);
        #    // locale_t newlocale(int __category_mask, const char* __locale_name, locale_t __base) __INTRODUCED_IN(21);
        #     // #endif /* __ANDROID_API__ >= 21 */
        #     // ...
        #     // #if __ANDROID_API__ >= 21
        #     // struct lconv* localeconv(void) __INTRODUCED_IN(21);
        #     // #endif /* __ANDROID_API__ >= 21 */
        # patch(self, patch_file=os.path.join(patch_folder, "localeconv.patch"))
        # }

        # patch(self, patch_file=os.path.join(patch_folder, "handle-iconv-failure.patch"))

        # backport
        # patch(self, patch_file=os.path.join(patch_folder, "utf82def_copy_safe.patch"))

    def package(self):
        cmake = CMake(self)
        cmake.install()

        license_folder = os.path.join(self.package_folder, "licenses")
        copy(self, "LICENSE", self.source_folder, license_folder)
        copy(self, "COPYING.gplv3", self.source_folder, license_folder)

        for f in ["applications", "icons", "man", "metainfo", "mime"]:
            rmdir(self, os.path.join(self.package_folder, "share", f))

    def package_info(self):
        self.cpp_info.libs = ["fontforge"]
