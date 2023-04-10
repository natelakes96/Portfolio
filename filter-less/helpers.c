#include "helpers.h"
#include <math.h>

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    // keep all red green and blue values locked together.
    // find average of all of them and make that the new rgb value
    for ( int h = 0; h < height; h++)
    {
        for (int w = 0; w < width; w++)
        {
            int avg = round((image[h][w].rgbtRed + image[h][w].rgbtGreen + image[h][w].rgbtBlue) / 3.0);
            image[h][w].rgbtRed = avg;
            image[h][w].rgbtBlue = avg;
            image[h][w].rgbtGreen = avg;
        }
    }
    return;
}

// Convert image to sepia
int min_max(int rgb)
{
    if(rgb > 255)
    {
        return 255;
    }
    else if (rgb < 0)
    {
        return 0;
    }
    else
    {
        return rgb;
    }

}
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    //run that sepia formula
    for (int h = 0; h < height; h++)
    {
        for (int w = 0; w < width; w++)
        {
            int RED = min_max(round((.393 * image[h][w].rgbtRed) + (.769 * image[h][w].rgbtGreen) + (.189 * image[h][w].rgbtBlue)));
            int GREEN = min_max(round((.349 * image[h][w].rgbtRed) + (.686 * image[h][w].rgbtGreen) + (.168 * image[h][w].rgbtBlue)));
            int BLUE = min_max(round((.272 * image[h][w].rgbtRed) +(.534 * image[h][w].rgbtGreen) + (.131 * image[h][w].rgbtBlue)));

            image[h][w].rgbtRed = RED;
            image[h][w].rgbtGreen = GREEN;
            image[h][w].rgbtBlue = BLUE;
        }
    }
    return;
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    // flipit
    RGBTRIPLE wait;

    for (int h = 0; h < height; h++)
        {
            for (int w = 0; w < width / 2; w++)
            {
                wait = image[h][w];
                image[h][w] = image[h][width - w - 1];
                image[h][width - w -1] = wait;
            }
        }
    return;
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    RGBTRIPLE copy[height][width];

    for (int h = 0; h < height; h++)
    {
        for (int w = 0; w < width; w++)
        {
            float sumBlue = 0;
            float sumGreen = 0;
            float sumRed = 0;
            float counter = 0;

            for (int i = -1; i < 2; i++)
            {
                for (int j = -1; j < 2; j++)
                {
                    if (h + i < 0 || h + i > height - 1)
                    {
                        continue;
                    }

                    if (w + j < 0 || w + j > width - 1)
                    {
                        continue;
                    }

                    sumBlue += image[h + i][w + j].rgbtBlue;
                    sumGreen += image[h + i][w + j].rgbtGreen;
                    sumRed += image[h + i][w + j].rgbtRed;
                    counter++;
                }
            }

            copy[h][w].rgbtBlue = round(sumBlue / counter);
            copy[h][w].rgbtGreen = round(sumGreen / counter);
            copy[h][w].rgbtRed = round(sumRed / counter);
        }
    }

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            image[i][j].rgbtBlue = copy[i][j].rgbtBlue;
            image[i][j].rgbtGreen = copy[i][j].rgbtGreen;
            image[i][j].rgbtRed = copy[i][j].rgbtRed;
        }

    }

    return;
}


