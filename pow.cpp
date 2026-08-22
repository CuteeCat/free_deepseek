// g++ -O3 -fopenmp pow.cpp -o pow.exe
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <atomic>
#ifdef _OPENMP
#include <omp.h>
#endif

static const uint64_t RC[24] = {
    0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808AULL,0x8000000080008000ULL,
    0x000000000000808BULL,0x0000000080000001ULL,0x8000000080008081ULL,0x8000000000008009ULL,
    0x000000000000008AULL,0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000AULL,
    0x000000008000808BULL,0x800000000000008BULL,0x8000000000008089ULL,0x8000000000008003ULL,
    0x8000000000008002ULL,0x8000000000000080ULL,0x000000000000800AULL,0x800000008000000AULL,
    0x8000000080008081ULL,0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL};
static const int ROT[5][5] = {
    {0,36,3,41,18},{1,44,10,45,2},{62,6,43,15,61},{28,55,25,21,56},{27,20,39,8,14}};

static inline uint64_t rol(uint64_t x, int n){ return (x << n) | (x >> (64 - n)); }
static inline uint64_t load_le(const uint8_t* p){  // little-endian 64-bit
    uint64_t v = 0;
    for (int i = 0; i < 8; i++) v |= (uint64_t)p[i] << (8 * i);
    return v;
}

// DeepSeekHashV1: SHA3-256(rate=136,pad=0x06), 23 轮 Keccak-f (RC[1..23])
static void keccak_f(uint64_t s[25]){
    for (int rnd = 1; rnd < 24; rnd++){
        uint64_t c[5], b[25];
        for (int x = 0; x < 5; x++) c[x] = s[x]^s[x+5]^s[x+10]^s[x+15]^s[x+20];
        for (int x = 0; x < 5; x++){
            uint64_t d = c[(x+4)%5] ^ rol(c[(x+1)%5], 1);
            for (int y = 0; y < 5; y++) s[x+5*y] ^= d;
        }
        for (int x = 0; x < 5; x++)
            for (int y = 0; y < 5; y++)
                b[y+5*((2*x+3*y)%5)] = rol(s[x+5*y], ROT[x][y]);
        for (int x = 0; x < 5; x++)
            for (int y = 0; y < 5; y++)
                s[x+5*y] = b[x+5*y] ^ (~b[(x+1)%5+5*y] & b[(x+2)%5+5*y]);
        s[0] ^= RC[rnd];
    }
}
static void deepseek_hash(const uint8_t* in, size_t len, uint8_t out[32]){
    const int rate = 136;
    uint64_t s[25] = {0};
    while (len >= (size_t)rate){
        for (int i = 0; i < 17; i++) s[i] ^= load_le(in + 8*i);
        keccak_f(s); in += rate; len -= rate;
    }
    uint8_t block[136] = {0};
    memcpy(block, in, len);
    block[len] = 0x06;
    block[rate-1] |= 0x80;
    for (int i = 0; i < 17; i++) s[i] ^= load_le(block + 8*i);
    keccak_f(s);
    for (int i = 0; i < 4; i++) memcpy(out + 8*i, &s[i], 8); // LE 输出 32 字节
}

int main(int argc, char** argv){
    if (argc < 5){ fprintf(stderr, "usage: pow.exe <salt> <expire_at> <difficulty> <challenge>\n"); return 1; }
    std::string salt = argv[1];
    uint64_t expire   = strtoull(argv[2], nullptr, 10);
    uint64_t diff     = strtoull(argv[3], nullptr, 10);
    std::string ch_hex = argv[4];

    uint8_t target[32];
    for (int i = 0; i < 32; i++){
        auto hex = [](char c){ return (c <= '9') ? c-'0' : (c|0x20)-'a'+10; };
        target[i] = (uint8_t)((hex(ch_hex[2*i]) << 4) | hex(ch_hex[2*i+1]));
    }
    std::string prefix = salt + "_" + std::to_string(expire) + "_";

    std::atomic<int> found{-1};
#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (int64_t n = 0; n < (int64_t)diff; n++){
        std::string pre = prefix + std::to_string(n);
        uint8_t out[32];
        deepseek_hash((const uint8_t*)pre.data(), pre.size(), out);
        if (memcmp(out, target, 32) == 0){
#ifdef _OPENMP
#pragma omp critical
#endif
            if (found.load() == -1) found.store((int)n);
        }
    }
    if (found.load() == -1){ fprintf(stderr, "no solution\n"); return 2; }
    printf("%d\n", found.load());
    return 0;
}