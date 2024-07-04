package cache

import (
	"fmt"
	"time"

	cache "github.com/patrickmn/go-cache"
)

type InMemoryConfig struct {
	DefaultExpiration int32
	CleanupInterval   int32
}

// InMemoryCache holds an instance to the memory back cache driver
type InMemoryCache struct {
	mem *cache.Cache
}

// NewCacheInstance returns c (i.e. cache instance).
func NewCacheInstance(conf *InMemoryConfig) (*InMemoryCache, error) {
	defaultExpiration := time.Duration(conf.DefaultExpiration) * time.Minute
	cleanupInterval := time.Duration(conf.CleanupInterval) * time.Minute
	instance := cache.New(defaultExpiration, cleanupInterval)
	return &InMemoryCache{
		mem: instance,
	}, nil
}

// Set - Refer cache.Cache.Set
func (imc *InMemoryCache) Set(key string, value string, ttl time.Duration) error {
	imc.mem.Set(key, value, ttl)
	return nil
}

// Get - Refer cache.Cache.Get
func (imc *InMemoryCache) Get(key string) (string, error) {
	val, found := imc.mem.Get(key)
	if !found {
		return "", fmt.Errorf("key provided does not exist")
	}
	return val.(string), nil
}

// Delete - Refer cache.Cache.Delete
func (imc *InMemoryCache) Delete(key string) error {
	imc.mem.Delete(key)
	return nil
}

func (imc *InMemoryCache) SAdd(string, []string) error {
	panic("This function is not implemented yet")
}

func (imc *InMemoryCache) SMembers(string) ([]string, error) {
	panic("This function is not implemented yet")
}

func (imc *InMemoryCache) SetExpiry(string, time.Duration) error {
	panic("This function is not implemented yet")
}

// Flush flushes all keys from cache. This is available only for memory cache
// and is helpful in tests.
func (imc *InMemoryCache) Flush() {
	imc.mem.Flush()
}