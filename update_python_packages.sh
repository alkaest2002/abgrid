#!/bin/zsh

# Get outdated packages as an array
outdated_packages=($(pip list --outdated --format=columns | tail -n +3 | awk '{print $1}'))

# Check if there are any outdated packages
if [ ${#outdated_packages[@]} -eq 0 ]; then
    echo "All packages are already up to date!"
    exit 0
fi

echo "Found the following outdated packages:"
printf '%s\n' "${outdated_packages[@]}"
echo
read "response? Do you want to update all ${#outdated_packages[@]} packages? (y/N): "

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Starting updates..."
    echo
    
    # Upgrade each package
    for package in "${outdated_packages[@]}"
    do
        echo "Upgrading $package..."
        pip install --upgrade "$package"
        if [ $? -eq 0 ]; then
            echo "✓ Successfully upgraded $package"
        else
            echo "✗ Failed to upgrade $package"
        fi
        echo "---"
    done
    
    echo "Update process completed!"
else
    echo "Update cancelled."
fi
