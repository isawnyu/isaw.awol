<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    version="1.0">
    
    <xsl:output method="html"/>
    
    <xsl:variable name="nl">
</xsl:variable>
    
    <xsl:template match="/">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="*[local-name()='span' and count(*) = 0 and normalize-space()='']"/>
    <xsl:template match="*[local-name()='div' and count(*) = 0 and normalize-space()='']"/>
    <xsl:template match="*[local-name()='span' and count(./@*) = 0]">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="*[local-name()='b']">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="*[local-name()='i']">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="*[local-name()='u']">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="*[local-name()='strong']">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="*[count(./@*) = 1 and ./@style]">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="*[local-name()='br' and not(following-sibling::*[local-name()='br'])]">
        <xsl:text>.</xsl:text>
    </xsl:template>
    <xsl:template match="*[local-name()='br' and count(../*) = 1]"/>
    <xsl:template match="*[local-name()='a'  and not(@href)]"/>       
    <xsl:template match="*[local-name()='a' and contains(@href, 'javascript')]"/>
    <xsl:template match="*[local-name()='a' and contains(@href, 'mailto')]"/>
    <xsl:template match="*[local-name()='a' and starts-with(@href, 'data:image')]"/>
    
    <xsl:template match="*[local-name()='img' and not(ancestor::*[local-name()='a'])]"/>
    <xsl:template match="*[local-name()='script']"/>
    
    <xsl:template match="*">
        <xsl:call-template name="copier"/>
    </xsl:template>
            
    <xsl:template name="copier">
        <xsl:param name="replace">no</xsl:param>
        <xsl:copy>
            <xsl:call-template name="clean-attributes"/>
            <xsl:choose>
                <xsl:when test="$replace='no'">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$replace"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:copy>
        <xsl:variable name="ename" select="local-name()"/>
        <xsl:choose>
            <xsl:when test="$ename='body'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h1'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h2'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h3'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h4'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h5'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='h6'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='p'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='ul'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='li'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='ol'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='br'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='hr'"><xsl:value-of select="$nl"/></xsl:when>
            <xsl:when test="$ename='div'"><xsl:value-of select="$nl"/></xsl:when>            
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="clean-attributes">
        <xsl:for-each select="@*">
            <xsl:variable name="aname" select="local-name(.)"/>
            <xsl:choose>
                <xsl:when test="$aname = 'width'"/>
                <xsl:when test="$aname = 'height'"/>
                <xsl:when test="$aname = 'onclick'"/>
                <xsl:when test="$aname = 'onmouseout'"/>
                <xsl:when test="$aname = 'onmouseover'"/>
                <xsl:when test="$aname = 'style'"/>
                <xsl:when test="$aname = 'valign'"/>
                <xsl:otherwise>
                    <xsl:copy-of select="."/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>
    
</xsl:stylesheet>