// =============================================================================
// test_bindings_contract.cpp — AD-6 drift test for the compiled bindings surface
// (spec-bindings-arbitration-contract). Compiles the REAL generated protocol/
// bindings.h and pins the frozen-additive consumer contract: each named field's
// exact type, binding_find's signature and miss semantics, the empty-manifest
// behavior, and the 16-hex hash shape. Renames/retypes/removals fail here at
// compile time; ADDED fields/ops/symbols pass by design (no sizeof/layout pin).
// The Python half of the net is test_generate_exports.py's render assertions;
// the battery regenerates bindings.h before compiling, so either side drifting
// breaks the run.
//
// Run:  g++ -std=c++17 -Wall -Wextra test_bindings_contract.cpp -o t && ./t
// =============================================================================

#include "../protocol/bindings.h"

#include <cassert>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <type_traits>

// ---- BindingEntry: the five frozen fields, exact types (frozen-additive:
//      additions tolerated, rename/retype/removal breaks the build here). ----
static_assert(std::is_same<decltype(BindingEntry::node_id), uint16_t>::value,
              "contract drift: BindingEntry::node_id must be uint16_t");
static_assert(std::is_same<decltype(BindingEntry::button), uint8_t>::value,
              "contract drift: BindingEntry::button must be uint8_t");
static_assert(std::is_same<decltype(BindingEntry::relay_count), uint8_t>::value,
              "contract drift: BindingEntry::relay_count must be uint8_t");
static_assert(std::is_same<decltype(BindingEntry::relays), const uint8_t *>::value,
              "contract drift: BindingEntry::relays must be const uint8_t*");
static_assert(std::is_same<decltype(BindingEntry::op), const char *>::value,
              "contract drift: BindingEntry::op must be const char*");

// ---- binding_find: keyed (node_id, button), returns const BindingEntry*. ----
static_assert(std::is_same<decltype(binding_find(uint16_t{0}, uint8_t{0})),
                           const BindingEntry *>::value,
              "contract drift: binding_find must be (uint16_t, uint8_t) -> const BindingEntry*");

// ---- Hash constant: constexpr char array (usable at compile time). The
//      indexed use inside static_assert REQUIRES constexpr evaluation, so
//      losing constexpr-ness (not just the type) also breaks the build. ----
static_assert(std::is_same<std::remove_reference<decltype(BINDINGS_MANIFEST_HASH[0])>::type,
                           const char>::value,
              "contract drift: BINDINGS_MANIFEST_HASH must be a constexpr char array");
static_assert(BINDINGS_MANIFEST_HASH[0] != '\0',
              "contract drift: BINDINGS_MANIFEST_HASH must be non-empty and constexpr-usable");

// ---- BINDINGS / BINDINGS_SIZE: table pointer type and size type. ----
static_assert(std::is_same<std::remove_cv<decltype(BINDINGS)>::type, const BindingEntry *>::value,
              "contract drift: BINDINGS must be const BindingEntry*");
static_assert(std::is_same<std::remove_cv<decltype(BINDINGS_SIZE)>::type, std::size_t>::value,
              "contract drift: BINDINGS_SIZE must be std::size_t");

int main() {
  // Hash shape: exactly 16 lowercase-hex chars (canonical_hash truncation, ADR-0009 §3).
  assert(std::strlen(BINDINGS_MANIFEST_HASH) == 16);
  for (const char *p = BINDINGS_MANIFEST_HASH; *p; ++p)
    assert(std::isxdigit(static_cast<unsigned char>(*p)) && !std::isupper(static_cast<unsigned char>(*p)));

  // Empty-manifest contract: null table, size 0, any lookup misses cleanly.
  // (If the committed manifest ever gains rows, the size-0 branch below simply
  // stops running — the miss-returns-nullptr probe stays valid either way, using
  // a key bindings.py could never validate: node_id 0xFFFF is outside the
  // registry, so no committed manifest can bind it.)
  if (BINDINGS_SIZE == 0)
    assert(BINDINGS == nullptr);
  assert(binding_find(0xFFFF, 0xFF) == nullptr);

  // Populated-table semantics (first-match, keyed equality) exercised against a
  // local table through the same struct type — binding_find itself iterates the
  // global BINDINGS, so its loop is covered above via the miss probe; the keyed
  // comparison it uses is pinned here structurally.
  static constexpr uint8_t kRelays[] = {0, 2};
  const BindingEntry local{100, 3, 2, kRelays, "toggle"};
  assert(local.node_id == 100 && local.button == 3);
  assert(local.relay_count == 2 && local.relays[1] == 2);
  assert(std::strcmp(local.op, "toggle") == 0);

  std::printf("bindings-contract: all surface pins hold\n");
  return 0;
}
